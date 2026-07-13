package com.inventory.mobile.rfid

import com.facebook.react.bridge.Arguments
import com.facebook.react.bridge.Promise
import com.facebook.react.bridge.ReactApplicationContext
import com.facebook.react.bridge.ReactContextBaseJavaModule
import com.facebook.react.bridge.ReactMethod
import com.facebook.react.modules.core.DeviceEventManagerModule
import java.lang.reflect.InvocationHandler
import java.lang.reflect.Proxy

class RscjaDeviceApiModule(
  reactContext: ReactApplicationContext
) : ReactContextBaseJavaModule(reactContext) {

  companion object {
    private const val MODULE_NAME = "RscjaDeviceApiModule"
    private const val TAG_EVENT_NAME = "onRfidTag"
  }

  private var readerInstance: Any? = null
  private var initialized = false
  private var inventoryCallbackProxy: Any? = null

  override fun getName(): String = MODULE_NAME

  @ReactMethod
  fun addListener(eventName: String?) {
    // Required for NativeEventEmitter compatibility.
  }

  @ReactMethod
  fun removeListeners(count: Int) {
    // Required for NativeEventEmitter compatibility.
  }

  @ReactMethod
  fun initialize(promise: Promise) {
    try {
      if (initialized && readerInstance != null) {
        promise.resolve(true)
        return
      }

      val readerClass = Class.forName("com.rscja.deviceapi.RFIDWithUHFUART")
      val getInstanceMethod = readerClass.getMethod("getInstance")
      val instance = getInstanceMethod.invoke(null)
        ?: throw IllegalStateException("RFIDWithUHFUART.getInstance() returned null")

      val initMethod = readerClass.getMethod("init", android.content.Context::class.java)
      val initResult = initMethod.invoke(instance, reactApplicationContext.applicationContext)
      val ok = when (initResult) {
        is Boolean -> initResult
        else -> false
      }

      if (!ok) {
        promise.reject("INIT_FAILED", "RFID SDK init(context) returned false")
        return
      }

      readerInstance = instance
      initialized = true
      promise.resolve(true)
    } catch (t: Throwable) {
      initialized = false
      readerInstance = null
      promise.reject("INIT_ERROR", t.message, t)
    }
  }

  @ReactMethod
  fun startInventory(promise: Promise) {
    try {
      val instance = readerInstance
        ?: throw IllegalStateException("Reader not initialized. Call initialize() first.")

      ensureInventoryCallback(instance)

      val startMethod = instance.javaClass.getMethod("startInventoryTag")
      val result = startMethod.invoke(instance)
      val ok = when (result) {
        is Boolean -> result
        else -> false
      }

      if (!ok) {
        promise.reject("START_FAILED", "RFID SDK startInventoryTag() returned false")
        return
      }

      promise.resolve(true)
    } catch (t: Throwable) {
      promise.reject("START_ERROR", t.message, t)
    }
  }

  @ReactMethod
  fun stopInventory(promise: Promise) {
    try {
      val instance = readerInstance
      if (instance == null) {
        promise.resolve(true)
        return
      }

      val stopMethod = instance.javaClass.getMethod("stopInventory")
      stopMethod.invoke(instance)
      promise.resolve(true)
    } catch (t: Throwable) {
      promise.reject("STOP_ERROR", t.message, t)
    }
  }

  @ReactMethod
  fun free(promise: Promise) {
    try {
      val instance = readerInstance
      if (instance != null) {
        try {
          instance.javaClass.getMethod("stopInventory").invoke(instance)
        } catch (_: Throwable) {
        }
        instance.javaClass.getMethod("free").invoke(instance)
      }

      inventoryCallbackProxy = null
      readerInstance = null
      initialized = false
      promise.resolve(true)
    } catch (t: Throwable) {
      promise.reject("FREE_ERROR", t.message, t)
    }
  }

  private fun ensureInventoryCallback(instance: Any) {
    if (inventoryCallbackProxy != null) return

    val callbackInterfaceClass = Class.forName("com.rscja.deviceapi.interfaces.IUHFInventoryCallback")
    val handler = InvocationHandler { _, method, args ->
      if (method.name == "callback") {
        val tagInfo = args?.firstOrNull()
        emitTag(tagInfo)
      }
      null
    }

    val callbackProxy = Proxy.newProxyInstance(
      callbackInterfaceClass.classLoader,
      arrayOf(callbackInterfaceClass),
      handler
    )

    val setCallbackMethod = instance.javaClass.getMethod("setInventoryCallback", callbackInterfaceClass)
    setCallbackMethod.invoke(instance, callbackProxy)

    inventoryCallbackProxy = callbackProxy
  }

  private fun emitTag(tagInfo: Any?) {
    val epc = extractEpc(tagInfo)
    if (epc.isBlank()) return

    val payload = Arguments.createMap().apply {
      putString("epc", epc)

      val rssiValue = extractRssi(tagInfo)
      if (rssiValue != null) {
        putDouble("rssi", rssiValue)
      }
    }

    reactApplicationContext
      .getJSModule(DeviceEventManagerModule.RCTDeviceEventEmitter::class.java)
      .emit(TAG_EVENT_NAME, payload)
  }

  private fun extractEpc(tagInfo: Any?): String {
    if (tagInfo == null) return ""

    val methodCandidates = listOf("getEPC", "getEpc", "getTagEPC", "epc")
    for (methodName in methodCandidates) {
      try {
        val value = tagInfo.javaClass.getMethod(methodName).invoke(tagInfo)
        val epc = value?.toString()?.trim().orEmpty()
        if (epc.isNotEmpty()) return epc
      } catch (_: Throwable) {
      }
    }

    return ""
  }

  private fun extractRssi(tagInfo: Any?): Double? {
    if (tagInfo == null) return null

    val methodCandidates = listOf("getRssi", "getRSSI")
    for (methodName in methodCandidates) {
      try {
        val value = tagInfo.javaClass.getMethod(methodName).invoke(tagInfo)
        return when (value) {
          is Number -> value.toDouble()
          is String -> value.toDoubleOrNull()
          else -> null
        }
      } catch (_: Throwable) {
      }
    }

    return null
  }
}
