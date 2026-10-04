import { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  Button,
  StyleSheet,
  Alert,
  FlatList,
  TouchableOpacity,
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';

const API_URL = 'http://booklocal-backend-alb-1738618234.eu-west-1.elb.amazonaws.com';

export default function App() {
  const [email, setEmail] = useState('customer@test.com');
  const [password, setPassword] = useState('securepass123');
  const [loggedIn, setLoggedIn] = useState(false);
  const [token, setToken] = useState('');
  const [date, setDate] = useState('2026-09-26');
  const [slots, setSlots] = useState<string[]>([]);
  const [loadingSlots, setLoadingSlots] = useState(false);

  const handleLogin = async () => {
    try {
      const response = await fetch(`${API_URL}/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });
      const data = await response.json();
      if (!response.ok) {
        Alert.alert('Login failed', data.detail || 'Unknown error');
        return;
      }
      await AsyncStorage.setItem('access_token', data.access_token);
      setToken(data.access_token);
      setLoggedIn(true);
    } catch (error) {
      Alert.alert('Error', 'Could not reach the server');
      console.error(error);
    }
  };

  const fetchSlots = async () => {
    setLoadingSlots(true);
    try {
      const response = await fetch(
        `${API_URL}/businesses/1/available-slots?service_id=1&date=${date}`
      );
      const data = await response.json();
      if (!response.ok) {
        Alert.alert('Error', data.detail || 'Could not load slots');
        setSlots([]);
        return;
      }
      setSlots(data.slots || []);
    } catch (error) {
      Alert.alert('Error', 'Could not reach the server');
      console.error(error);
    } finally {
      setLoadingSlots(false);
    }
  };

  const bookSlot = async (time: string) => {
    try {
      const startTime = `${date}T${time}:00`;
      const response = await fetch(`${API_URL}/bookings`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          business_id: 1,
          service_id: 1,
          start_time: startTime,
        }),
      });
      const data = await response.json();
      if (!response.ok) {
        Alert.alert('Booking failed', data.detail || 'Unknown error');
        return;
      }
      Alert.alert('Booked!', `Confirmed for ${time} on ${date}`);
      fetchSlots();
    } catch (error) {
      Alert.alert('Error', 'Could not reach the server');
      console.error(error);
    }
  };

  if (!loggedIn) {
    return (
      <View style={styles.container}>
        <Text style={styles.title}>BookLocal</Text>
        <TextInput
          style={styles.input}
          placeholder="Email"
          placeholderTextColor="#999999"
          value={email}
          onChangeText={setEmail}
          autoCapitalize="none"
        />
        <TextInput
          style={styles.input}
          placeholder="Password"
          placeholderTextColor="#999999"
          value={password}
          onChangeText={setPassword}
          secureTextEntry
        />
        <Button title="Log In" onPress={handleLogin} />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Test Barbershop</Text>
      <Text style={styles.subtitle}>Haircut — €20 — 30 min</Text>

      <TextInput
        style={styles.input}
        placeholder="Date (YYYY-MM-DD)"
        placeholderTextColor="#999999"
        value={date}
        onChangeText={setDate}
      />
      <Button title="Check Available Slots" onPress={fetchSlots} />

      {loadingSlots && <Text style={styles.loading}>Loading...</Text>}

      <FlatList
        data={slots}
        keyExtractor={(item) => item}
        style={styles.list}
        renderItem={({ item }) => (
          <TouchableOpacity style={styles.slot} onPress={() => bookSlot(item)}>
            <Text style={styles.slotText}>{item}</Text>
          </TouchableOpacity>
        )}
        ListEmptyComponent={
          !loadingSlots ? <Text style={styles.empty}>No slots loaded yet</Text> : null
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 24, paddingTop: 60, backgroundColor: '#ffffff' },
  title: { fontSize: 28, fontWeight: 'bold', textAlign: 'center', color: '#000000' },
  subtitle: { fontSize: 16, textAlign: 'center', color: '#555555', marginBottom: 16 },
  input: {
    borderWidth: 1,
    borderColor: '#cccccc',
    borderRadius: 8,
    padding: 12,
    marginBottom: 12,
    color: '#000000',
    backgroundColor: '#ffffff',
  },
  loading: { textAlign: 'center', marginVertical: 8, color: '#000000' },
  list: { marginTop: 16 },
  slot: {
    backgroundColor: '#f0f0f0',
    padding: 14,
    borderRadius: 8,
    marginBottom: 8,
  },
  slotText: { fontSize: 16, textAlign: 'center', color: '#000000' },
  empty: { textAlign: 'center', color: '#999999', marginTop: 20 },
});
