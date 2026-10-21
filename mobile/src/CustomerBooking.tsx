import { useEffect, useMemo, useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  ActivityIndicator,
} from 'react-native';
import { api, errText } from './api';

type Service = { id: number; name: string; price: number; duration_minutes: number };
type Business = {
  id: number;
  name: string;
  category: string | null;
  location: string | null;
  slug: string;
  services: Service[];
  hours: { day_of_week: number; opening_time: string; closing_time: string }[];
};
type Confirmed = {
  id: number;
  start_time: string;
  end_time: string;
  cancel_token: string;
  serviceName: string;
};

const pad = (n: number) => String(n).padStart(2, '0');
const dateKey = (d: Date) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;

export default function CustomerBooking({ slug, onBack }: { slug: string; onBack?: () => void }) {
  const [biz, setBiz] = useState<Business | null>(null);
  const [loadError, setLoadError] = useState('');
  const [service, setService] = useState<Service | null>(null);
  const [date, setDate] = useState<string | null>(null);
  const [slots, setSlots] = useState<string[]>([]);
  const [loadingSlots, setLoadingSlots] = useState(false);
  const [slot, setSlot] = useState<string | null>(null);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [confirmed, setConfirmed] = useState<Confirmed | null>(null);
  const [askCancel, setAskCancel] = useState(false);
  const [cancelled, setCancelled] = useState(false);

  useEffect(() => {
    (async () => {
      const res = await api(`/public/businesses/${slug}`, null);
      if (res.ok) setBiz(res.data);
      else if (res.status === 404) setLoadError("We couldn't find that business. Check the code and try again.");
      else setLoadError(errText(res.data));
    })();
  }, [slug]);

  const dateOptions = useMemo(() => {
    if (!biz) return [];
    const openDays = new Set(biz.hours.map((h) => h.day_of_week));
    const out: { value: string; label: string }[] = [];
    const today = new Date();
    for (let i = 0; i < 28 && out.length < 14; i++) {
      const d = new Date(today.getFullYear(), today.getMonth(), today.getDate() + i);
      const dow = (d.getDay() + 6) % 7; // Monday = 0, like the backend
      if (!openDays.has(dow)) continue;
      out.push({
        value: dateKey(d),
        label: d.toLocaleDateString('en-IE', { weekday: 'short', day: 'numeric', month: 'short' }),
      });
    }
    return out;
  }, [biz]);

  const loadSlots = async (bizId: number, svc: Service, day: string) => {
    setLoadingSlots(true);
    setSlots([]);
    setSlot(null);
    const res = await api(
      `/businesses/${bizId}/available-slots?service_id=${svc.id}&date=${day}`,
      null
    );
    setLoadingSlots(false);
    if (!res.ok) {
      setError(errText(res.data));
      return;
    }
    let list: string[] = res.data.slots || [];
    if (day === dateKey(new Date())) {
      const now = new Date();
      const current = `${pad(now.getHours())}:${pad(now.getMinutes())}`;
      list = list.filter((t) => t > current);
    }
    setSlots(list);
  };

  const pickService = (svc: Service) => {
    setService(svc);
    setDate(null);
    setSlots([]);
    setSlot(null);
    setError('');
  };

  const pickDate = (day: string) => {
    if (!biz || !service) return;
    setDate(day);
    setError('');
    loadSlots(biz.id, service, day);
  };

  const submit = async () => {
    if (!biz || !service || !date || !slot) return;
    setError('');
    if (!name.trim()) {
      setError('Please enter your name');
      return;
    }
    if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email.trim())) {
      setError('Please enter a valid email address');
      return;
    }
    setBusy(true);
    const res = await api(`/public/businesses/${slug}/bookings`, null, {
      method: 'POST',
      body: JSON.stringify({
        service_id: service.id,
        start_time: `${date}T${slot}:00`,
        name: name.trim(),
        email: email.trim(),
        phone: phone.trim() || null,
      }),
    });
    setBusy(false);
    if (res.status === 409) {
      setError('Sorry, that time was just taken. Please pick another.');
      loadSlots(biz.id, service, date);
      return;
    }
    if (!res.ok) {
      setError(errText(res.data));
      return;
    }
    setConfirmed({ ...res.data, serviceName: service.name });
  };

  const cancel = async () => {
    if (!confirmed) return;
    const res = await api(`/public/bookings/${confirmed.cancel_token}`, null, { method: 'DELETE' });
    if (res.ok) setCancelled(true);
    else setError(errText(res.data));
  };

  const reset = () => {
    setService(null);
    setDate(null);
    setSlots([]);
    setSlot(null);
    setConfirmed(null);
    setAskCancel(false);
    setCancelled(false);
    setError('');
  };

  const back = onBack ? (
    <TouchableOpacity onPress={onBack}>
      <Text style={styles.back}>‹ Back</Text>
    </TouchableOpacity>
  ) : null;

  if (!biz && !loadError) {
    return (
      <View style={[styles.page, { justifyContent: 'center' }]}>
        <ActivityIndicator />
      </View>
    );
  }

  if (!biz) {
    return (
      <View style={styles.page}>
        {back}
        <Text style={styles.error}>{loadError}</Text>
      </View>
    );
  }

  if (confirmed) {
    return (
      <ScrollView contentContainerStyle={styles.page}>
        {cancelled ? (
          <>
            <Text style={styles.title}>Booking cancelled</Text>
            <Text style={styles.subtitle}>Your appointment has been cancelled.</Text>
          </>
        ) : (
          <>
            <Text style={styles.title}>You're booked!</Text>
            <View style={styles.summary}>
              <Text style={styles.summaryName}>{biz.name}</Text>
              <Text style={styles.summaryLine}>{confirmed.serviceName}</Text>
              <Text style={styles.summaryLine}>
                {confirmed.start_time.slice(0, 10)} at {confirmed.start_time.slice(11, 16)}
              </Text>
              {biz.location ? <Text style={styles.meta}>{biz.location}</Text> : null}
            </View>
            {askCancel ? (
              <View>
                <Text style={styles.subtitle}>Cancel this appointment?</Text>
                <TouchableOpacity style={styles.dangerButton} onPress={cancel}>
                  <Text style={styles.buttonText}>Yes, cancel it</Text>
                </TouchableOpacity>
                <TouchableOpacity onPress={() => setAskCancel(false)}>
                  <Text style={styles.link}>No, keep it</Text>
                </TouchableOpacity>
              </View>
            ) : (
              <TouchableOpacity onPress={() => setAskCancel(true)}>
                <Text style={[styles.link, { color: '#d11a2a' }]}>Cancel this booking</Text>
              </TouchableOpacity>
            )}
          </>
        )}
        {error ? <Text style={styles.error}>{error}</Text> : null}
        <TouchableOpacity style={styles.button} onPress={reset}>
          <Text style={styles.buttonText}>Book another appointment</Text>
        </TouchableOpacity>
        {back}
      </ScrollView>
    );
  }

  return (
    <ScrollView contentContainerStyle={styles.page} keyboardShouldPersistTaps="handled">
      {back}
      <Text style={styles.title}>{biz.name}</Text>
      {biz.location ? <Text style={styles.subtitle}>{biz.location}</Text> : null}

      <Text style={styles.section}>1. Choose a service</Text>
      {biz.services.length === 0 ? (
        <Text style={styles.meta}>This business hasn't added any services yet.</Text>
      ) : (
        biz.services.map((sv) => (
          <TouchableOpacity
            key={sv.id}
            style={[styles.card, service?.id === sv.id && styles.cardActive]}
            onPress={() => pickService(sv)}
          >
            <Text style={styles.cardTitle}>{sv.name}</Text>
            <Text style={styles.meta}>
              EUR {sv.price.toFixed(2)} · {sv.duration_minutes} min
            </Text>
          </TouchableOpacity>
        ))
      )}

      {service ? (
        <>
          <Text style={styles.section}>2. Choose a day</Text>
          {dateOptions.length === 0 ? (
            <Text style={styles.meta}>No opening days are set up yet.</Text>
          ) : (
            <View style={styles.chips}>
              {dateOptions.map((d) => (
                <TouchableOpacity
                  key={d.value}
                  style={[styles.chip, date === d.value && styles.chipActive]}
                  onPress={() => pickDate(d.value)}
                >
                  <Text style={[styles.chipText, date === d.value && styles.chipTextActive]}>
                    {d.label}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          )}
        </>
      ) : null}

      {service && date ? (
        <>
          <Text style={styles.section}>3. Choose a time</Text>
          {loadingSlots ? (
            <ActivityIndicator />
          ) : slots.length === 0 ? (
            <Text style={styles.meta}>No times left on this day. Try another day.</Text>
          ) : (
            <View style={styles.chips}>
              {slots.map((t) => (
                <TouchableOpacity
                  key={t}
                  style={[styles.chip, slot === t && styles.chipActive]}
                  onPress={() => setSlot(t)}
                >
                  <Text style={[styles.chipText, slot === t && styles.chipTextActive]}>{t}</Text>
                </TouchableOpacity>
              ))}
            </View>
          )}
        </>
      ) : null}

      {service && date && slot ? (
        <>
          <Text style={styles.section}>4. Your details</Text>
          <TextInput
            style={styles.input}
            placeholder="Your name"
            placeholderTextColor="#999999"
            value={name}
            onChangeText={setName}
          />
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
            placeholder="Phone (optional)"
            placeholderTextColor="#999999"
            value={phone}
            onChangeText={setPhone}
            keyboardType="phone-pad"
          />
          <TouchableOpacity style={styles.button} onPress={submit} disabled={busy}>
            <Text style={styles.buttonText}>
              {busy ? 'Booking...' : `Confirm ${service.name} at ${slot}`}
            </Text>
          </TouchableOpacity>
        </>
      ) : null}

      {error ? <Text style={styles.error}>{error}</Text> : null}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  page: {
    flexGrow: 1,
    padding: 24,
    paddingTop: 60,
    backgroundColor: '#ffffff',
    width: '100%',
    maxWidth: 520,
    alignSelf: 'center',
  },
  back: { color: '#007aff', fontSize: 16, marginBottom: 12 },
  title: { fontSize: 28, fontWeight: 'bold', textAlign: 'center', color: '#000000' },
  subtitle: { fontSize: 15, textAlign: 'center', color: '#555555', marginBottom: 12 },
  section: { fontSize: 17, fontWeight: 'bold', color: '#222222', marginTop: 22, marginBottom: 10 },
  meta: { fontSize: 14, color: '#666666', marginTop: 2 },
  card: { backgroundColor: '#f0f0f0', padding: 14, borderRadius: 8, marginBottom: 8 },
  cardActive: { backgroundColor: '#dbeaff', borderWidth: 1, borderColor: '#007aff' },
  cardTitle: { fontSize: 16, fontWeight: 'bold', color: '#000000' },
  chips: { flexDirection: 'row', flexWrap: 'wrap' },
  chip: {
    borderWidth: 1,
    borderColor: '#cccccc',
    borderRadius: 20,
    paddingVertical: 8,
    paddingHorizontal: 14,
    marginRight: 8,
    marginBottom: 8,
  },
  chipActive: { backgroundColor: '#007aff', borderColor: '#007aff' },
  chipText: { color: '#333333', fontSize: 15 },
  chipTextActive: { color: '#ffffff', fontWeight: 'bold' },
  input: {
    borderWidth: 1,
    borderColor: '#cccccc',
    borderRadius: 8,
    padding: 12,
    marginBottom: 12,
    color: '#000000',
    backgroundColor: '#ffffff',
  },
  button: {
    backgroundColor: '#007aff',
    padding: 14,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 8,
  },
  dangerButton: {
    backgroundColor: '#d11a2a',
    padding: 14,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 8,
  },
  buttonText: { color: '#ffffff', fontSize: 16, fontWeight: 'bold' },
  link: { textAlign: 'center', color: '#007aff', marginTop: 16, fontSize: 15 },
  error: { color: '#d11a2a', marginTop: 14, fontSize: 15, textAlign: 'center' },
  summary: { backgroundColor: '#f0f0f0', padding: 16, borderRadius: 8, marginVertical: 16 },
  summaryName: { fontSize: 18, fontWeight: 'bold', color: '#000000' },
  summaryLine: { fontSize: 16, color: '#222222', marginTop: 4 },
});
