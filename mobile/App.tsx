import { useEffect, useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  Alert,
  FlatList,
  RefreshControl,
  ActivityIndicator,
  ScrollView,
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { api, errText } from './src/api';

const TOKEN_KEY = 'owner_token';
const CATEGORIES = ['Barber', 'Salon', 'Coach', 'Other'];

type Booking = {
  id: number;
  start_time: string;
  end_time: string;
  status: string;
  service: string;
  customer_name: string;
  customer_email: string;
  customer_phone: string | null;
};

function AuthScreen({ onToken }: { onToken: (t: string) => void }) {
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [busy, setBusy] = useState(false);

  const submit = async () => {
    setBusy(true);
    const res =
      mode === 'register'
        ? await api('/register', null, {
            method: 'POST',
            body: JSON.stringify({ name, email: email.trim().toLowerCase(), password }),
          })
        : await api('/login', null, {
            method: 'POST',
            body: JSON.stringify({ email: email.trim().toLowerCase(), password }),
          });
    setBusy(false);
    if (!res.ok) {
      Alert.alert(mode === 'register' ? 'Sign up failed' : 'Login failed', errText(res.data));
      return;
    }
    onToken(res.data.access_token);
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>BookLocal</Text>
      <Text style={styles.subtitle}>For business owners</Text>
      {mode === 'register' && (
        <TextInput
          style={styles.input}
          placeholder="Your name"
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
      <TouchableOpacity style={styles.primaryButton} onPress={submit} disabled={busy}>
        <Text style={styles.primaryButtonText}>
          {busy ? 'Please wait...' : mode === 'login' ? 'Log In' : 'Create Account'}
        </Text>
      </TouchableOpacity>
      <TouchableOpacity onPress={() => setMode(mode === 'login' ? 'register' : 'login')}>
        <Text style={styles.link}>
          {mode === 'login' ? 'New here? Create an account' : 'Already have an account? Log in'}
        </Text>
      </TouchableOpacity>
    </View>
  );
}

function SetupScreen({ token, onCreated }: { token: string; onCreated: (b: any) => void }) {
  const [name, setName] = useState('');
  const [category, setCategory] = useState('Barber');
  const [location, setLocation] = useState('');
  const [busy, setBusy] = useState(false);

  const create = async () => {
    if (name.trim().length < 2) {
      Alert.alert('Business name', 'Please enter your business name');
      return;
    }
    setBusy(true);
    const res = await api('/owner/business', token, {
      method: 'POST',
      body: JSON.stringify({
        name: name.trim(),
        category: category.toLowerCase(),
        location: location.trim() || null,
      }),
    });
    setBusy(false);
    if (!res.ok) {
      Alert.alert('Could not create business', errText(res.data));
      return;
    }
    onCreated(res.data);
  };

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.title}>Set up your business</Text>
      <Text style={styles.subtitle}>You can change the details later</Text>
      <TextInput
        style={styles.input}
        placeholder="Business name"
        placeholderTextColor="#999999"
        value={name}
        onChangeText={setName}
      />
      <Text style={styles.label}>What kind of business?</Text>
      <View style={styles.chips}>
        {CATEGORIES.map((c) => (
          <TouchableOpacity
            key={c}
            style={[styles.chip, category === c && styles.chipActive]}
            onPress={() => setCategory(c)}
          >
            <Text style={[styles.chipText, category === c && styles.chipTextActive]}>{c}</Text>
          </TouchableOpacity>
        ))}
      </View>
      <TextInput
        style={styles.input}
        placeholder="Town / location (optional)"
        placeholderTextColor="#999999"
        value={location}
        onChangeText={setLocation}
      />
      <TouchableOpacity style={styles.primaryButton} onPress={create} disabled={busy}>
        <Text style={styles.primaryButtonText}>{busy ? 'Creating...' : 'Create Business'}</Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

function BookingsTab({ token }: { token: string }) {
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    const res = await api('/owner/bookings', token);
    setLoading(false);
    if (!res.ok) {
      Alert.alert('Error', errText(res.data));
      return;
    }
    const today = new Date().toISOString().slice(0, 10);
    const upcoming = (res.data as Booking[]).filter(
      (b) => b.status === 'confirmed' && b.start_time.slice(0, 10) >= today
    );
    setBookings(upcoming);
  };

  useEffect(() => {
    load();
  }, []);

  return (
    <FlatList
      data={bookings}
      keyExtractor={(b) => String(b.id)}
      refreshControl={<RefreshControl refreshing={loading} onRefresh={load} />}
      ListEmptyComponent={
        !loading ? <Text style={styles.empty}>No upcoming bookings yet</Text> : null
      }
      renderItem={({ item, index }) => {
        const date = item.start_time.slice(0, 10);
        const showDate = index === 0 || bookings[index - 1].start_time.slice(0, 10) !== date;
        return (
          <View>
            {showDate && <Text style={styles.dateHeader}>{date}</Text>}
            <View style={styles.card}>
              <Text style={styles.cardTime}>
                {item.start_time.slice(11, 16)} – {item.end_time.slice(11, 16)}
              </Text>
              <Text style={styles.cardService}>{item.service}</Text>
              <Text style={styles.cardCustomer}>{item.customer_name}</Text>
              {item.customer_phone ? (
                <Text style={styles.cardMeta}>{item.customer_phone}</Text>
              ) : null}
              <Text style={styles.cardMeta}>{item.customer_email}</Text>
            </View>
          </View>
        );
      }}
    />
  );
}

function Home({ token, business, onLogout }: { token: string; business: any; onLogout: () => void }) {
  const [tab, setTab] = useState<'bookings' | 'services' | 'hours'>('bookings');
  const tabs: Array<['bookings' | 'services' | 'hours', string]> = [
    ['bookings', 'Bookings'],
    ['services', 'Services'],
    ['hours', 'Hours'],
  ];

  return (
    <View style={styles.container}>
      <Text style={styles.title}>{business.name}</Text>
      <Text style={styles.subtitle}>Booking link: {business.slug}</Text>
      <View style={styles.tabs}>
        {tabs.map(([key, label]) => (
          <TouchableOpacity
            key={key}
            style={[styles.tab, tab === key && styles.tabActive]}
            onPress={() => setTab(key)}
          >
            <Text style={[styles.tabText, tab === key && styles.tabTextActive]}>{label}</Text>
          </TouchableOpacity>
        ))}
      </View>
      <View style={styles.body}>
        {tab === 'bookings' && <BookingsTab token={token} />}
        {tab === 'services' && <Text style={styles.empty}>Services: coming next</Text>}
        {tab === 'hours' && <Text style={styles.empty}>Opening hours: coming next</Text>}
      </View>
      <TouchableOpacity onPress={onLogout}>
        <Text style={styles.logout}>Log out</Text>
      </TouchableOpacity>
    </View>
  );
}

export default function App() {
  const [booting, setBooting] = useState(true);
  const [token, setToken] = useState<string | null>(null);
  const [business, setBusiness] = useState<any>(null);
  const [needsSetup, setNeedsSetup] = useState(false);

  const enter = async (t: string) => {
    const res = await api('/owner/business', t);
    if (res.status === 401) {
      await AsyncStorage.removeItem(TOKEN_KEY);
      setToken(null);
      return;
    }
    if (res.ok) {
      setBusiness(res.data);
      setNeedsSetup(false);
    } else if (res.status === 404) {
      setNeedsSetup(true);
    } else {
      Alert.alert('Error', errText(res.data));
      return;
    }
    await AsyncStorage.setItem(TOKEN_KEY, t);
    setToken(t);
  };

  useEffect(() => {
    (async () => {
      const saved = await AsyncStorage.getItem(TOKEN_KEY);
      if (saved) await enter(saved);
      setBooting(false);
    })();
  }, []);

  const logout = async () => {
    await AsyncStorage.removeItem(TOKEN_KEY);
    setToken(null);
    setBusiness(null);
    setNeedsSetup(false);
  };

  if (booting) {
    return (
      <View style={[styles.container, { justifyContent: 'center' }]}>
        <ActivityIndicator />
      </View>
    );
  }
  if (!token) return <AuthScreen onToken={enter} />;
  if (needsSetup || !business) {
    return (
      <SetupScreen
        token={token}
        onCreated={(b) => {
          setBusiness(b);
          setNeedsSetup(false);
        }}
      />
    );
  }
  return <Home token={token} business={business} onLogout={logout} />;
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 24, paddingTop: 60, backgroundColor: '#ffffff' },
  title: { fontSize: 28, fontWeight: 'bold', textAlign: 'center', color: '#000000' },
  subtitle: { fontSize: 15, textAlign: 'center', color: '#555555', marginBottom: 16 },
  label: { fontSize: 15, color: '#333333', marginBottom: 8 },
  input: {
    borderWidth: 1,
    borderColor: '#cccccc',
    borderRadius: 8,
    padding: 12,
    marginBottom: 12,
    color: '#000000',
    backgroundColor: '#ffffff',
  },
  primaryButton: {
    backgroundColor: '#007aff',
    padding: 14,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 4,
  },
  primaryButtonText: { color: '#ffffff', fontSize: 16, fontWeight: 'bold' },
  link: { textAlign: 'center', color: '#007aff', marginTop: 16, fontSize: 15 },
  chips: { flexDirection: 'row', flexWrap: 'wrap', marginBottom: 12 },
  chip: {
    borderWidth: 1,
    borderColor: '#cccccc',
    borderRadius: 20,
    paddingVertical: 8,
    paddingHorizontal: 16,
    marginRight: 8,
    marginBottom: 8,
  },
  chipActive: { backgroundColor: '#007aff', borderColor: '#007aff' },
  chipText: { color: '#333333', fontSize: 15 },
  chipTextActive: { color: '#ffffff', fontWeight: 'bold' },
  tabs: { flexDirection: 'row', marginBottom: 12 },
  tab: { flex: 1, padding: 10, borderBottomWidth: 2, borderBottomColor: '#dddddd' },
  tabActive: { borderBottomColor: '#007aff' },
  tabText: { textAlign: 'center', color: '#888888', fontSize: 16 },
  tabTextActive: { color: '#007aff', fontWeight: 'bold' },
  body: { flex: 1 },
  empty: { textAlign: 'center', color: '#999999', marginTop: 24 },
  dateHeader: { fontSize: 15, fontWeight: 'bold', color: '#333333', marginTop: 12, marginBottom: 6 },
  card: { backgroundColor: '#f0f0f0', padding: 14, borderRadius: 8, marginBottom: 8 },
  cardTime: { fontSize: 17, fontWeight: 'bold', color: '#000000' },
  cardService: { fontSize: 15, color: '#007aff', marginTop: 2 },
  cardCustomer: { fontSize: 16, color: '#000000', marginTop: 6 },
  cardMeta: { fontSize: 14, color: '#555555', marginTop: 2 },
  logout: { textAlign: 'center', color: '#888888', paddingVertical: 12 },
});
