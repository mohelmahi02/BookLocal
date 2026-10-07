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

type MyBooking = { id: number; start_time: string; status: string };

const todayString = () => {
  const d = new Date();
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
};

export default function App() {
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loggedIn, setLoggedIn] = useState(false);
  const [token, setToken] = useState('');
  const [tab, setTab] = useState<'book' | 'mine'>('book');
  const [date, setDate] = useState(todayString());
  const [slots, setSlots] = useState<string[]>([]);
  const [loadingSlots, setLoadingSlots] = useState(false);
  const [bookings, setBookings] = useState<MyBooking[]>([]);
  const [loadingBookings, setLoadingBookings] = useState(false);

  const login = async (loginEmail: string, loginPassword: string) => {
    const response = await fetch(`${API_URL}/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: loginEmail, password: loginPassword }),
    });
    const data = await response.json();
    if (!response.ok) {
      Alert.alert('Login failed', data.detail || 'Unknown error');
      return;
    }
    await AsyncStorage.setItem('access_token', data.access_token);
    setToken(data.access_token);
    setLoggedIn(true);
  };

  const handleLogin = async () => {
    try {
      await login(email, password);
    } catch (error) {
      Alert.alert('Error', 'Could not reach the server');
      console.error(error);
    }
  };

  const handleRegister = async () => {
    try {
      const response = await fetch(`${API_URL}/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, email, password }),
      });
      const data = await response.json();
      if (!response.ok) {
        Alert.alert('Registration failed', data.detail || 'Unknown error');
        return;
      }
      await login(email, password);
    } catch (error) {
      Alert.alert('Error', 'Could not reach the server');
      console.error(error);
    }
  };

  const handleLogout = async () => {
    await AsyncStorage.removeItem('access_token');
    setToken('');
    setLoggedIn(false);
    setSlots([]);
    setBookings([]);
    setTab('book');
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

  const fetchBookings = async (authToken: string = token) => {
    setLoadingBookings(true);
    try {
      const response = await fetch(`${API_URL}/bookings`, {
        headers: { Authorization: `Bearer ${authToken}` },
      });
      const data = await response.json();
      if (!response.ok) {
        Alert.alert('Error', data.detail || 'Could not load bookings');
        return;
      }
      setBookings(data.filter((b: MyBooking) => b.status !== 'cancelled'));
    } catch (error) {
      Alert.alert('Error', 'Could not reach the server');
      console.error(error);
    } finally {
      setLoadingBookings(false);
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

  const cancelBooking = (id: number) => {
    Alert.alert('Cancel booking?', 'This will free up the slot.', [
      { text: 'Keep it', style: 'cancel' },
      {
        text: 'Cancel booking',
        style: 'destructive',
        onPress: async () => {
          try {
            const response = await fetch(`${API_URL}/bookings/${id}`, {
              method: 'DELETE',
              headers: { Authorization: `Bearer ${token}` },
            });
            if (!response.ok) {
              const data = await response.json();
              Alert.alert('Error', data.detail || 'Could not cancel');
              return;
            }
            fetchBookings();
          } catch (error) {
            Alert.alert('Error', 'Could not reach the server');
            console.error(error);
          }
        },
      },
    ]);
  };

  const formatTime = (iso: string) => {
    const [d, t] = iso.split('T');
    return `${d} at ${(t || '').slice(0, 5)}`;
  };

  if (!loggedIn) {
    return (
      <View style={styles.container}>
        <Text style={styles.title}>BookLocal</Text>
        <Text style={styles.subtitle}>
          {mode === 'login' ? 'Log in to book' : 'Create an account'}
        </Text>
        {mode === 'register' && (
          <TextInput
            style={styles.input}
            placeholder="Name"
            placeholderTextColor="#999999"
            value={name}
            onChangeText={setName}
          />
        )}
        <TextInput
          style={styles.input}
          placeholder="Email"
          placeholderTextColor="#999999"
          value={email}
          onChangeText={setEmail}
          autoCapitalize="none"
          keyboardType="email-address"
        />
        <TextInput
          style={styles.input}
          placeholder="Password"
          placeholderTextColor="#999999"
          value={password}
          onChangeText={setPassword}
          secureTextEntry
        />
        <Button
          title={mode === 'login' ? 'Log In' : 'Register'}
          onPress={mode === 'login' ? handleLogin : handleRegister}
        />
        <TouchableOpacity
          onPress={() => setMode(mode === 'login' ? 'register' : 'login')}
        >
          <Text style={styles.link}>
            {mode === 'login'
              ? "Don't have an account? Register"
              : 'Already have an account? Log in'}
          </Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Test Barbershop</Text>
      <Text style={styles.subtitle}>Haircut — €20 — 30 min</Text>

      <View style={styles.tabs}>
        <TouchableOpacity
          style={[styles.tab, tab === 'book' && styles.tabActive]}
          onPress={() => setTab('book')}
        >
          <Text style={[styles.tabText, tab === 'book' && styles.tabTextActive]}>
            Book
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tab, tab === 'mine' && styles.tabActive]}
          onPress={() => {
            setTab('mine');
            fetchBookings();
          }}
        >
          <Text style={[styles.tabText, tab === 'mine' && styles.tabTextActive]}>
            My Bookings
          </Text>
        </TouchableOpacity>
      </View>

      {tab === 'book' ? (
        <>
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
        </>
      ) : (
        <>
          {loadingBookings && <Text style={styles.loading}>Loading...</Text>}
          <FlatList
            data={bookings}
            keyExtractor={(item) => String(item.id)}
            style={styles.list}
            renderItem={({ item }) => (
              <View style={styles.bookingRow}>
                <Text style={styles.bookingText}>{formatTime(item.start_time)}</Text>
                <TouchableOpacity onPress={() => cancelBooking(item.id)}>
                  <Text style={styles.cancel}>Cancel</Text>
                </TouchableOpacity>
              </View>
            )}
            ListEmptyComponent={
              !loadingBookings ? <Text style={styles.empty}>No bookings yet</Text> : null
            }
          />
        </>
      )}

      <Button title="Log out" color="#888888" onPress={handleLogout} />
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
  link: { textAlign: 'center', color: '#007aff', marginTop: 16, fontSize: 15 },
  loading: { textAlign: 'center', marginVertical: 8, color: '#000000' },
  list: { marginTop: 16, flex: 1 },
  slot: {
    backgroundColor: '#f0f0f0',
    padding: 14,
    borderRadius: 8,
    marginBottom: 8,
  },
  slotText: { fontSize: 16, textAlign: 'center', color: '#000000' },
  empty: { textAlign: 'center', color: '#999999', marginTop: 20 },
  tabs: { flexDirection: 'row', marginBottom: 16 },
  tab: {
    flex: 1,
    padding: 10,
    borderBottomWidth: 2,
    borderBottomColor: '#dddddd',
  },
  tabActive: { borderBottomColor: '#007aff' },
  tabText: { textAlign: 'center', color: '#888888', fontSize: 16 },
  tabTextActive: { color: '#007aff', fontWeight: 'bold' },
  bookingRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#f0f0f0',
    padding: 14,
    borderRadius: 8,
    marginBottom: 8,
  },
  bookingText: { fontSize: 16, color: '#000000' },
  cancel: { color: '#d11a2a', fontWeight: 'bold', fontSize: 15 },
});
