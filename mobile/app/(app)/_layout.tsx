import { Redirect, Stack } from "expo-router";
import { useAuth } from "../../src/context/auth-context";
import { ActivityIndicator, View } from "react-native";

export default function AppLayout() {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <View style={{ flex: 1, justifyContent: "center", alignItems: "center" }}>
        <ActivityIndicator size="large" color="#1a56db" />
      </View>
    );
  }

  if (!isAuthenticated) {
    return <Redirect href="/login" />;
  }

  return (
    <Stack
      screenOptions={{
        headerStyle: { backgroundColor: "#1a56db" },
        headerTintColor: "#fff",
        headerTitleStyle: { fontWeight: "700" },
      }}
    >
      <Stack.Screen name="dashboard" options={{ title: "Dashboard" }} />
      <Stack.Screen name="add-asset" options={{ title: "Add Asset" }} />
      <Stack.Screen name="scan-asset" options={{ title: "Scan Asset", headerShown: false }} />
      <Stack.Screen name="asset-detail" options={{ title: "Asset Details" }} />
    </Stack>
  );
}
