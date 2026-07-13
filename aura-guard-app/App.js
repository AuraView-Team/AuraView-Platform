import React, { useState, useEffect } from 'react';
import { StyleSheet, Text, View, TextInput, TouchableOpacity, SafeAreaView, Platform } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import io from 'socket.io-client';
import * as Notifications from 'expo-notifications';
import { WebView } from 'react-native-webview';

Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: false,
  }),
});

// =========================================================================
// 🚀 PRODUCTION BACKEND CONFIGURATION
// =========================================================================
// When your backend is deployed live (Render, Vercel, Railway, etc.),
// simply paste your live URL inside the quotes below (e.g., 'https://auraview.onrender.com').
// If testing locally on WiFi, put your laptop's IP address (e.g., 'http://192.168.1.2:8000').
const DEFAULT_BACKEND_URL = 'http://192.168.1.2:8000';

export default function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [guardId, setGuardId] = useState('');
  const [pin, setPin] = useState('');
  const [backendUrl, setBackendUrl] = useState(DEFAULT_BACKEND_URL);
  
  const [socket, setSocket] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [latestAlert, setLatestAlert] = useState(null);
  const [stats, setStats] = useState({ count: 0, alert_status: 'SAFE' });

  useEffect(() => {
    loadSavedData();
    requestPermissions();
  }, []);

  const requestPermissions = async () => {
    const { status } = await Notifications.requestPermissionsAsync();
    if (status !== 'granted') {
      alert('Push notification permissions are required to receive alerts!');
    }
  };

  const loadSavedData = async () => {
    const savedUrl = await AsyncStorage.getItem('backendUrl');
    const savedGuard = await AsyncStorage.getItem('guardId');
    if (savedUrl) setBackendUrl(savedUrl);
    if (savedGuard) setGuardId(savedGuard);
  };

  const handleLogin = async () => {
    if (!guardId || !pin || !backendUrl) {
      alert('Please fill all fields');
      return;
    }
    try {
      const response = await fetch(`${backendUrl}/guard_login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ guard_id: guardId, pin: pin, fcm_token: 'pending_app_generation' })
      });
      const data = await response.json();
      
      if (data.success) {
        await AsyncStorage.setItem('backendUrl', backendUrl);
        await AsyncStorage.setItem('guardId', guardId);
        if (data.guard && data.guard.site_id) {
          await AsyncStorage.setItem('siteId', data.guard.site_id);
        }
        connectSocket(backendUrl, data.guard?.site_id);
        setIsLoggedIn(true);
      } else {
        alert(data.message || 'Login failed: Invalid ID or PIN');
      }
    } catch (e) {
      alert('Could not connect to backend server at ' + backendUrl);
    }
  };

  const connectSocket = (url, siteId) => {
    const newSocket = io(url, { 
      path: '/ws', 
      transports: ['websocket'] 
    });
    
    newSocket.on('connect', () => {
      setIsConnected(true);
      if (siteId) {
        newSocket.emit('join_site', { site_id: siteId });
      }
    });
    newSocket.on('disconnect', () => setIsConnected(false));
    
    newSocket.on('security_alert', async (data) => {
      setLatestAlert(data);
      // Trigger loud local push notification
      await Notifications.scheduleNotificationAsync({
        content: {
          title: "🚨 EMERGENCY ALERT!",
          body: data.message,
          sound: true,
          priority: Notifications.AndroidNotificationPriority.MAX,
        },
        trigger: null,
      });
    });

    newSocket.on('broadcast_data', (data) => {
      setStats(data);
    });

    setSocket(newSocket);
  };

  const handleAcknowledge = () => {
    if (socket && latestAlert) {
      socket.emit('acknowledge_alert', {
        guardId: guardId,
        timestamp: Date.now(),
        alertInfo: latestAlert
      });
      alert('Alert Acknowledged! Admin Dashboard has been notified.');
      setLatestAlert(null);
    }
  };

  const handleLogout = async () => {
    if (socket) {
      socket.disconnect();
      setSocket(null);
    }
    setIsLoggedIn(false);
    setIsConnected(false);
    setStats({ count: 0, alert_status: 'SAFE' });
    setLatestAlert(null);
  };

  if (!isLoggedIn) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loginCard}>
          <Text style={styles.title}>Aura Guard</Text>
          <Text style={styles.subtitle}>Security Personnel Portal</Text>
          
          <Text style={styles.label}>Backend IP Address</Text>
          <TextInput
            style={styles.input}
            placeholder="e.g., http://192.168.1.x:8000"
            placeholderTextColor="#ADB5BD"
            value={backendUrl}
            onChangeText={setBackendUrl}
            autoCapitalize="none"
          />
          <Text style={styles.label}>Mobile Number</Text>
          <TextInput 
            style={styles.input} 
            placeholder="e.g. 9876543210" 
            placeholderTextColor="#888"
            keyboardType="numeric"
            value={guardId}
            onChangeText={setGuardId}
          />
          <Text style={styles.label}>Secure PIN</Text>
          <TextInput
            style={styles.input}
            placeholder="****"
            placeholderTextColor="#ADB5BD"
            value={pin}
            onChangeText={setPin}
            secureTextEntry
            keyboardType="numeric"
          />
          
          <TouchableOpacity style={styles.button} onPress={handleLogin}>
            <Text style={styles.buttonText}>LOGIN SECURELY</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      {/* Box 1: Header / Profile */}
      <View style={[styles.card, styles.headerCard]}>
        <View>
          <Text style={styles.headerTitle}>Aura Guard</Text>
          <Text style={styles.headerSubtitle}>No: {guardId}</Text>
        </View>
        <View style={styles.statusBadge}>
          <Text style={{ color: isConnected ? '#2B8A3E' : '#E03131', fontWeight: 'bold', fontSize: 11 }}>
            {isConnected ? '🟢 CONNECTED' : '🔴 OFFLINE'}
          </Text>
        </View>
      </View>

      {/* Box 2: Crowd Status Meter */}
      <View style={[styles.card, styles.statsCard]}>
        <Text style={styles.cardTitle}>Live Crowd Status</Text>
        <Text style={[styles.statusText, { color: stats.alert_status === 'DANGER' ? '#E03131' : '#2B8A3E' }]}>
          {stats.alert_status}
        </Text>
        <Text style={styles.countText}>{stats.count} people detected</Text>
      </View>

      {/* Box 3: Live Camera Feed */}
      <View style={[styles.card, styles.videoCard]}>
        <Text style={styles.cardTitle}>Live Camera Feed</Text>
        <View style={styles.webViewWrapper}>
          {isConnected ? (
            <WebView
              source={{ uri: `${backendUrl}/video_feed` }}
              style={styles.webview}
              scrollEnabled={false}
              showsVerticalScrollIndicator={false}
              showsHorizontalScrollIndicator={false}
            />
          ) : (
            <View style={styles.offlineVideo}>
              <Text style={styles.offlineText}>Camera Disconnected</Text>
            </View>
          )}
        </View>
      </View>

      {/* Box 4: Action Center */}
      <View style={[styles.card, styles.actionCard]}>
        <Text style={styles.cardTitle}>Action Center</Text>
        
        {latestAlert && (
          <View style={styles.alertBox}>
            <Text style={styles.alertTitle}>🚨 ACTIVE EMERGENCY</Text>
            <Text style={styles.alertMessage}>{latestAlert.message}</Text>
            <TouchableOpacity style={styles.ackButton} onPress={handleAcknowledge}>
              <Text style={styles.ackButtonText}>ACKNOWLEDGE ALERT</Text>
            </TouchableOpacity>
          </View>
        )}

        <TouchableOpacity style={styles.logoutButton} onPress={handleLogout}>
          <Text style={styles.logoutButtonText}>🔴 Disconnect & Logout</Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F8F9FA',
    padding: 16,
    paddingTop: Platform.OS === 'android' ? 40 : 20,
  },
  card: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
    borderWidth: 1,
    borderColor: '#E9ECEF',
  },
  headerCard: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 14,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '900',
    color: '#212529',
  },
  headerSubtitle: {
    fontSize: 14,
    color: '#868E96',
    marginTop: 2,
    fontWeight: '600',
  },
  statusBadge: {
    backgroundColor: '#F8F9FA',
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: '#DEE2E6',
  },
  statsCard: {
    alignItems: 'center',
    paddingVertical: 24,
  },
  cardTitle: {
    fontSize: 12,
    fontWeight: 'bold',
    color: '#ADB5BD',
    textTransform: 'uppercase',
    letterSpacing: 1.5,
    marginBottom: 12,
  },
  statusText: {
    fontSize: 34,
    fontWeight: '900',
    marginBottom: 4,
    letterSpacing: 1,
  },
  countText: {
    fontSize: 16,
    color: '#495057',
    fontWeight: '600',
  },
  videoCard: {
    padding: 16,
  },
  webViewWrapper: {
    height: 180,
    borderRadius: 8,
    overflow: 'hidden',
    backgroundColor: '#E9ECEF',
  },
  webview: {
    flex: 1,
    backgroundColor: 'transparent',
  },
  offlineVideo: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  offlineText: {
    color: '#ADB5BD',
    fontWeight: 'bold',
    fontSize: 14,
  },
  actionCard: {
    padding: 16,
  },
  alertBox: {
    backgroundColor: '#FFF5F5',
    borderColor: '#FFE3E3',
    borderWidth: 1,
    padding: 16,
    borderRadius: 8,
    marginBottom: 16,
    alignItems: 'center',
  },
  alertTitle: {
    color: '#E03131',
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 8,
  },
  alertMessage: {
    color: '#495057',
    fontSize: 14,
    textAlign: 'center',
    marginBottom: 12,
    lineHeight: 20,
  },
  ackButton: {
    backgroundColor: '#E03131',
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 8,
    width: '100%',
    alignItems: 'center',
  },
  ackButtonText: {
    color: '#FFF',
    fontWeight: 'bold',
    fontSize: 13,
    letterSpacing: 0.5,
  },
  logoutButton: {
    backgroundColor: '#F8F9FA',
    borderWidth: 1,
    borderColor: '#DEE2E6',
    paddingVertical: 14,
    borderRadius: 8,
    alignItems: 'center',
  },
  logoutButtonText: {
    color: '#495057',
    fontWeight: 'bold',
    fontSize: 14,
  },
  // Login Styles
  loginCard: {
    flex: 1,
    justifyContent: 'center',
  },
  title: {
    fontSize: 30,
    fontWeight: '900',
    color: '#212529',
    textAlign: 'center',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 15,
    color: '#868E96',
    textAlign: 'center',
    marginBottom: 40,
    fontWeight: '500',
  },
  label: {
    color: '#495057',
    fontWeight: 'bold',
    marginBottom: 8,
    fontSize: 11,
    textTransform: 'uppercase',
    letterSpacing: 1,
  },
  input: {
    backgroundColor: '#FFFFFF',
    color: '#212529',
    borderRadius: 8,
    padding: 16,
    marginBottom: 20,
    borderWidth: 1,
    borderColor: '#DEE2E6',
    fontSize: 15,
  },
  button: {
    backgroundColor: '#4C6EF5',
    padding: 16,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 10,
    shadowColor: '#4C6EF5',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.2,
    shadowRadius: 8,
    elevation: 3,
  },
  buttonText: {
    color: '#FFFFFF',
    fontWeight: 'bold',
    fontSize: 14,
    letterSpacing: 1,
  },
});
