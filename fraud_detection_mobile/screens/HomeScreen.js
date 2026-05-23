import React, { useState } from 'react';
import { 
  StyleSheet, Text, View, TextInput, TouchableOpacity, 
  ScrollView, ActivityIndicator, Alert, KeyboardAvoidingView, Platform 
} from 'react-native';

// IP automático detectado pelo sistema
const API_URL = 'http://192.168.0.31:8000/predict'; 

const TRANSACTION_TYPES = ['TRANSFER', 'CASH_OUT', 'PAYMENT', 'DEBIT', 'CASH_IN'];

export default function HomeScreen({ navigation }) {
  const [loading, setLoading] = useState(false);
  const [type, setType] = useState('TRANSFER');
  const [amount, setAmount] = useState('');
  const [nameOrig, setNameOrig] = useState('');
  const [oldbalanceOrg, setOldbalanceOrg] = useState('');
  const [newbalanceOrig, setNewbalanceOrig] = useState('');
  const [nameDest, setNameDest] = useState('');
  const [oldbalanceDest, setOldbalanceDest] = useState('');
  const [newbalanceDest, setNewbalanceDest] = useState('');

  const applyPreset = (mode) => {
    if (mode === 'FRAUDE') {
      setType('TRANSFER');
      setAmount('500000.00');
      setNameOrig('C_HACKER_01');
      setOldbalanceOrg('500000.00');
      setNewbalanceOrig('0.00');
      setNameDest('C_RECEPTOR_99');
      setOldbalanceDest('0.00');
      setNewbalanceDest('0.00');
    } else {
      setType('CASH_OUT');
      setAmount('150.50');
      setNameOrig('C_USER_NORMAL');
      setOldbalanceOrg('1000.00');
      setNewbalanceOrig('849.50');
      setNameDest('M_LOJA_ABC');
      setOldbalanceDest('5000.00');
      setNewbalanceDest('5150.50');
    }
  };

  const handleAnalyze = async () => {
    if (!amount || !nameOrig || !nameDest) {
      Alert.alert("Erro", "Campos obrigatórios: Valor, Origem e Destino.");
      return;
    }

    setLoading(true);
    const payload = {
      transaction: {
        step: 1,
        type,
        amount: parseFloat(amount),
        nameOrig,
        oldbalanceOrg: parseFloat(oldbalanceOrg || 0),
        newbalanceOrig: parseFloat(newbalanceOrig || 0),
        nameDest,
        oldbalanceDest: parseFloat(oldbalanceDest || 0),
        newbalanceDest: parseFloat(newbalanceDest || 0),
      },
      infrastructure: "Local"
    };

    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      const data = await response.json();
      
      if (response.ok) {
        navigation.navigate('Result', { result: data, originalData: payload.transaction });
      } else {
        throw new Error(data.detail || "Erro na API");
      }
    } catch (error) {
      Alert.alert("Erro de Conexão", "Não foi possível conectar à API. Verifique se o servidor está rodando no IP 192.168.0.31.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView 
      behavior={Platform.OS === "ios" ? "padding" : "height"}
      style={styles.container}
    >
      <ScrollView showsVerticalScrollIndicator={false}>
        <Text style={styles.sectionTitle}>TIPO DE OPERAÇÃO</Text>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.chipsContainer}>
          {TRANSACTION_TYPES.map((t) => (
            <TouchableOpacity 
              key={t} 
              style={[styles.chip, type === t && styles.chipActive]} 
              onPress={() => setType(t)}
            >
              <Text style={[styles.chipText, type === t && styles.chipTextActive]}>{t}</Text>
            </TouchableOpacity>
          ))}
        </ScrollView>

        <View style={styles.form}>
          <Text style={styles.label}>VALOR DA TRANSAÇÃO (R$)*</Text>
          <TextInput style={styles.input} placeholder="0.00" placeholderTextColor="#5A5A7A" keyboardType="numeric" value={amount} onChangeText={setAmount} />

          <View style={styles.row}>
            <View style={{ flex: 1, marginRight: 8 }}>
              <Text style={styles.label}>ID ORIGEM*</Text>
              <TextInput style={styles.input} placeholder="C123..." placeholderTextColor="#5A5A7A" value={nameOrig} onChangeText={setNameOrig} />
            </View>
            <View style={{ flex: 1, marginLeft: 8 }}>
              <Text style={styles.label}>ID DESTINO*</Text>
              <TextInput style={styles.input} placeholder="C987..." placeholderTextColor="#5A5A7A" value={nameDest} onChangeText={setNameDest} />
            </View>
          </View>

          <Text style={styles.sectionTitle}>BALANÇO ORIGEM</Text>
          <View style={styles.row}>
            <View style={{ flex: 1, marginRight: 8 }}>
              <Text style={styles.label}>SALDO INICIAL</Text>
              <TextInput style={styles.input} keyboardType="numeric" value={oldbalanceOrg} onChangeText={setOldbalanceOrg} />
            </View>
            <View style={{ flex: 1, marginLeft: 8 }}>
              <Text style={styles.label}>SALDO FINAL</Text>
              <TextInput style={styles.input} keyboardType="numeric" value={newbalanceOrig} onChangeText={setNewbalanceOrig} />
            </View>
          </View>

          <Text style={styles.sectionTitle}>BALANÇO DESTINO</Text>
          <View style={styles.row}>
            <View style={{ flex: 1, marginRight: 8 }}>
              <Text style={styles.label}>SALDO INICIAL</Text>
              <TextInput style={styles.input} keyboardType="numeric" value={oldbalanceDest} onChangeText={setOldbalanceDest} />
            </View>
            <View style={{ flex: 1, marginLeft: 8 }}>
              <Text style={styles.label}>SALDO FINAL</Text>
              <TextInput style={styles.input} keyboardType="numeric" value={newbalanceDest} onChangeText={setNewbalanceDest} />
            </View>
          </View>
        </View>

        <View style={styles.presets}>
          <TouchableOpacity style={[styles.presetBtn, { borderColor: '#E05555' }]} onPress={() => applyPreset('FRAUDE')}>
            <Text style={[styles.presetText, { color: '#E05555' }]}>SIMULAR FRAUDE</Text>
          </TouchableOpacity>
          <TouchableOpacity style={[styles.presetBtn, { borderColor: '#2ECC8A' }]} onPress={() => applyPreset('LEGITIMA')}>
            <Text style={[styles.presetText, { color: '#2ECC8A' }]}>SIMULAR LEGÍTIMA</Text>
          </TouchableOpacity>
        </View>

        <TouchableOpacity style={styles.mainBtn} onPress={handleAnalyze} disabled={loading}>
          {loading ? <ActivityIndicator color="#FFF" /> : <Text style={styles.mainBtnText}>ANALISAR TRANSAÇÃO</Text>}
        </TouchableOpacity>
        <View style={{ height: 40 }} />
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0A0A0F', paddingHorizontal: 20 },
  sectionTitle: { color: '#5A5A7A', fontSize: 12, fontWeight: 'bold', marginTop: 24, marginBottom: 12, letterSpacing: 1 },
  chipsContainer: { flexDirection: 'row', marginBottom: 8 },
  chip: { paddingHorizontal: 16, paddingVertical: 8, borderRadius: 20, backgroundColor: '#12121C', borderWidth: 1, borderColor: '#1E1E30', marginRight: 8 },
  chipActive: { backgroundColor: '#4F6EF7', borderColor: '#4F6EF7' },
  chipText: { color: '#5A5A7A', fontSize: 13, fontWeight: '600' },
  chipTextActive: { color: '#FFF' },
  form: { marginTop: 10 },
  label: { color: '#5A5A7A', fontSize: 10, marginBottom: 6 },
  input: { backgroundColor: '#12121C', borderWidth: 1, borderColor: '#1E1E30', borderRadius: 12, padding: 14, color: '#EAEAF5', fontSize: 16, marginBottom: 16 },
  row: { flexDirection: 'row' },
  presets: { flexDirection: 'row', justifyContent: 'space-between', marginTop: 10 },
  presetBtn: { flex: 0.48, paddingVertical: 12, borderRadius: 12, borderWidth: 1, alignItems: 'center' },
  presetText: { fontSize: 11, fontWeight: 'bold' },
  mainBtn: { backgroundColor: '#4F6EF7', paddingVertical: 18, borderRadius: 14, marginTop: 30, alignItems: 'center', elevation: 4 },
  mainBtnText: { color: '#FFF', fontSize: 16, fontWeight: 'bold', letterSpacing: 1 },
});
