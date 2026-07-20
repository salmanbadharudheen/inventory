package com.inventory.mobile.rfid

import android.util.Log
import com.facebook.react.bridge.Arguments
import com.facebook.react.bridge.Promise
import com.facebook.react.bridge.ReactApplicationContext
import com.facebook.react.bridge.ReactContextBaseJavaModule
import com.facebook.react.bridge.ReactMethod
import com.facebook.react.bridge.WritableMap
import com.facebook.react.modules.core.DeviceEventManagerModule
import java.lang.reflect.InvocationHandler
import java.lang.reflect.Proxy

class RscjaDeviceApiModule(
  reactContext: ReactApplicationContext
) : ReactContextBaseJavaModule(reactContext) {

  companion object {
    private const val MODULE_NAME = "RscjaDeviceApiModule"
    private const val TAG_EVENT_NAME = "onRfidTag"
    private const val LOG_TAG = "RscjaDeviceApi"
    private const val SDK_READER_CLASS = "com.rscja.deviceapi.RFIDWithUHFUART"
    private const val SDK_CALLBACK_CLASS = "com.rscja.deviceapi.interfaces.IUHFInventoryCallback"
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
      ensureReaderInitialized()
      Log.d(LOG_TAG, "initialize(): success")
      promise.resolve(true)
    } catch (t: Throwable) {
      initialized = false
      readerInstance = null
      Log.e(LOG_TAG, "initialize(): error", t)
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
        Log.e(LOG_TAG, "startInventory(): startInventoryTag() returned false")
        promise.reject("START_FAILED", "RFID SDK startInventoryTag() returned false")
        return
      }

      Log.d(LOG_TAG, "startInventory(): success")
      promise.resolve(true)
    } catch (t: Throwable) {
      Log.e(LOG_TAG, "startInventory(): error", t)
      promise.reject("START_ERROR", t.message, t)
    }
  }

  @ReactMethod
  fun stopInventory(promise: Promise) {
    try {
      val instance = readerInstance
      if (instance == null) {
        Log.d(LOG_TAG, "stopInventory(): skipped (reader is null)")
        promise.resolve(true)
        return
      }

      val stopMethod = instance.javaClass.getMethod("stopInventory")
      stopMethod.invoke(instance)
      Log.d(LOG_TAG, "stopInventory(): success")
      promise.resolve(true)
    } catch (t: Throwable) {
      Log.e(LOG_TAG, "stopInventory(): error", t)
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
      Log.d(LOG_TAG, "free(): success")
      promise.resolve(true)
    } catch (t: Throwable) {
      Log.e(LOG_TAG, "free(): error", t)
      promise.reject("FREE_ERROR", t.message, t)
    }
  }

  @ReactMethod
  fun isSdkAvailable(promise: Promise) {
    try {
      Class.forName(SDK_READER_CLASS)
      Class.forName(SDK_CALLBACK_CLASS)
      promise.resolve(true)
    } catch (_: Throwable) {
      promise.resolve(false)
    }
  }

  @ReactMethod
  fun getDebugStatus(promise: Promise) {
    try {
      promise.resolve(buildDebugStatus())
    } catch (t: Throwable) {
      promise.reject("DEBUG_STATUS_ERROR", t.message, t)
    }
  }

  @ReactMethod
  fun testSdkBinding(promise: Promise) {
    try {
      val readerClass = Class.forName(SDK_READER_CLASS)
      readerClass.getMethod("getInstance")
      readerClass.getMethod("init", android.content.Context::class.java)
      readerClass.getMethod("startInventoryTag")
      readerClass.getMethod("stopInventory")
      readerClass.getMethod("free")
      val callbackClass = Class.forName(SDK_CALLBACK_CLASS)

      val result = Arguments.createMap().apply {
        putBoolean("ok", true)
        putString("readerClass", readerClass.name)
        putString("callbackClass", callbackClass.name)
      }
      promise.resolve(result)
    } catch (t: Throwable) {
      val result = Arguments.createMap().apply {
        putBoolean("ok", false)
        putString("error", t.message)
      }
      Log.e(LOG_TAG, "testSdkBinding(): error", t)
      promise.resolve(result)
    }
  }

  @ReactMethod
  fun setReaderPower(power: Int, promise: Promise) {
    try {
      if (power !in 5..30) {
        promise.reject("POWER_RANGE", "Power must be between 5 and 30 dBm.")
        return
      }

      val instance = ensureReaderInitialized()
      val attempt = trySetReaderPower(instance, power)
      val result = Arguments.createMap()

      if (attempt == null) {
        result.putBoolean("ok", false)
        result.putString("error", "No compatible set-power method found in DeviceAPI SDK.")
        promise.resolve(result)
        return
      }

      result.putBoolean("ok", attempt.second)
      result.putInt("power", power)
      result.putString("methodUsed", attempt.first)
      if (!attempt.second) {
        result.putString("error", "SDK method returned false while applying power.")
      }

      Log.d(LOG_TAG, "setReaderPower(): power=$power method=${attempt.first} ok=${attempt.second}")
      promise.resolve(result)
    } catch (t: Throwable) {
      Log.e(LOG_TAG, "setReaderPower(): error", t)
      promise.reject("SET_POWER_ERROR", t.message, t)
    }
  }

  @ReactMethod
  fun getReaderPower(promise: Promise) {
    try {
      val instance = ensureReaderInitialized()
      val powerInfo = tryGetReaderPower(instance)
      val result = Arguments.createMap()

      if (powerInfo == null) {
        result.putBoolean("ok", false)
        result.putString("error", "No compatible get-power method found in DeviceAPI SDK.")
        promise.resolve(result)
        return
      }

      result.putBoolean("ok", true)
      result.putInt("power", powerInfo.second)
      result.putString("methodUsed", powerInfo.first)
      promise.resolve(result)
    } catch (t: Throwable) {
      Log.e(LOG_TAG, "getReaderPower(): error", t)
      promise.reject("GET_POWER_ERROR", t.message, t)
    }
  }

  private fun ensureInventoryCallback(instance: Any) {
    if (inventoryCallbackProxy != null) return

    val callbackInterfaceClass = Class.forName(SDK_CALLBACK_CLASS)
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
    Log.d(LOG_TAG, "ensureInventoryCallback(): callback registered")
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

    Log.d(LOG_TAG, "emitTag(): EPC=$epc")
  }

  private fun buildDebugStatus(): WritableMap {
    return Arguments.createMap().apply {
      putBoolean("initialized", initialized)
      putBoolean("hasReaderInstance", readerInstance != null)
      putBoolean("hasInventoryCallback", inventoryCallbackProxy != null)
      putBoolean("readerClassAvailable", classAvailable(SDK_READER_CLASS))
      putBoolean("callbackClassAvailable", classAvailable(SDK_CALLBACK_CLASS))
      putString("readerInstanceClass", readerInstance?.javaClass?.name)
    }
  }

  private fun ensureReaderInitialized(): Any {
    if (initialized && readerInstance != null) {
      Log.d(LOG_TAG, "ensureReaderInitialized(): already initialized")
      return readerInstance as Any
    }

    val readerClass = Class.forName(SDK_READER_CLASS)
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
      throw IllegalStateException("RFID SDK init(context) returned false")
    }

    readerInstance = instance
    initialized = true
    return instance
  }

  private fun trySetReaderPower(instance: Any, power: Int): Pair<String, Boolean>? {
    val candidateMethods = listOf(
      "setPower",
      "setOutputPower",
      "setPowerLevel",
      "setReaderPower",
      "setRFPower"
    )

    for (methodName in candidateMethods) {
      val result = invokeIntArgBooleanMethod(instance, methodName, power)
      if (result != null) {
        return methodName to result
      }
    }

    return null
  }

  private fun tryGetReaderPower(instance: Any): Pair<String, Int>? {
    val candidateMethods = listOf(
      "getPower",
      "getOutputPower",
      "getPowerLevel",
      "getReaderPower",
      "getRFPower"
    )

    for (methodName in candidateMethods) {
      try {
        val method = instance.javaClass.getMethod(methodName)
        val value = method.invoke(instance)
        val power = when (value) {
          is Number -> value.toInt()
          is String -> value.toIntOrNull()
          else -> null
        }
        if (power != null) {
          return methodName to power
        }
      } catch (_: NoSuchMethodException) {
      } catch (_: Throwable) {
      }
    }

    return null
  }

  private fun invokeIntArgBooleanMethod(instance: Any, methodName: String, value: Int): Boolean? {
    val paramTypes = listOf(
      Int::class.javaPrimitiveType,
      Int::class.java
    )

    for (paramType in paramTypes) {
      try {
        val method = instance.javaClass.getMethod(methodName, paramType)
        val result = method.invoke(instance, value)
        return when (result) {
          is Boolean -> result
          else -> true
        }
      } catch (_: NoSuchMethodException) {
      } catch (_: Throwable) {
        return false
      }
    }

    return null
  }

  private fun classAvailable(className: String): Boolean {
    return try {
      Class.forName(className)
      true
    } catch (_: Throwable) {
      false
    }
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
