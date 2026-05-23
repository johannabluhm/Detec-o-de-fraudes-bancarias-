import React, { useEffect, useRef } from 'react';
import { StyleSheet, Text, View, Animated, TouchableOpacity, ScrollView } from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';

export default function ResultScreen({ route, navigation }) {
  const { result, originalData } = route.params;
  const isFraud = result.is_fraud;
  
  const barWidth = useRef(new Animated.Value(0)).current;
  const scaleAnim = useRef(new Animated.Value(0)).current;

  const errorBalanceOrig = originalData.oldbalanceOrg - originalData.amount - originalData.newbalanceOrig;
  const errorBalanceDest = originalData.oldbalanceDest + originalData.amount - originalData.newbalanceDest;

  useEffect(() => {
    Animated.parallel([
      Animated.spring(scaleAnim, { toValue: 1, friction: 4, useNativeDriver: true }),
      Animated.timing(barWidth, {
        toValue: result.fraud_probability * 100,
        duration: 1000,
        useNativeDriver: false,
      })
    ]).start();
  }, []);

  const color = isFraud ? '#E05555' : '#2ECC8A';

  return (
    <ScrollView style={styles.container} showsVerticalScrollIndicator={false}>
      <Animated.View style={[styles.header, { transform: [{ scale: scaleAnim }] }]}>
        <MaterialCommunityIcons name={isFraud ? "shield-alert" : "shield-check"} size={100} color={color} />
        <Text style={[styles.verdictText, { color }]}>
          {isFraud ? "FRAUDE DETECTADA" : "TRANSAÇÃO LEGÍTIMA"}
        </Text>
      </Animated.View>

      <View style={styles.card}>
        <Text style={styles.cardLabel}>PROBABILIDADE DE RISCO</Text>
        <Text style={[styles.probValue, { color }]}>{(result.fraud_probability * 100).toFixed(1)}%</Text>
        <View style={styles.barBg}>
          <Animated.View style={[styles.barFill, { backgroundColor: color, width: barWidth.interpolate({
            inputRange: [0, 100],
            outputRange: ['0%', '100%']
          }) }]} />
        </View>
      </View>

      <Text style={styles.sectionTitle}>ANÁLISE DE CONSISTÊNCIA</Text>
      <View style={styles.card}>
        <View style={styles.detailRow}>
          <Text style={styles.detailLabel}>Erro Balanço Origem:</Text>
          <Text style={[styles.detailValue, errorBalanceOrig !== 0 && { color: '#E05555' }]}>
            R$ {errorBalanceOrig.toFixed(2)}
          </Text>
        </View>
        <View style={styles.detailRow}>
          <Text style={styles.detailLabel}>Erro Balanço Destino:</Text>
          <Text style={[styles.detailValue, errorBalanceDest !== 0 && { color: '#E05555' }]}>
            R$ {errorBalanceDest.toFixed(2)}
          </Text>
        </View>
        <View style={styles.infoBox}>
          <MaterialCommunityIcons name="information-outline" size={16} color="#5A5A7A" />
          <Text style={styles.infoText}>O modelo usa inconsistências contábeis como principal sinal de fraude.</Text>
        </View>
      </View>

      <Text style={styles.sectionTitle}>DETALHES DA TRANSAÇÃO</Text>
      <View style={styles.card}>
        {[
          { label: "Valor", value: `R$ ${originalData.amount.toFixed(2)}` },
          { label: "Tipo", value: originalData.type },
          { label: "ID Origem", value: originalData.nameOrig },
          { label: "Saldo Origem", value: `R$ ${originalData.oldbalanceOrg.toFixed(2)}` },
          { label: "ID Destino", value: originalData.nameDest }
        ].map((item, i) => (
          <View key={i} style={styles.detailRow}>
            <Text style={styles.detailLabel}>{item.label}:</Text>
            <Text style={styles.detailValue}>{item.value}</Text>
          </View>
        ))}
      </View>

      <TouchableOpacity style={styles.backBtn} onPress={() => navigation.goBack()}>
        <Text style={styles.backBtnText}>← NOVA ANÁLISE</Text>
      </TouchableOpacity>
      <View style={{ height: 40 }} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0A0A0F', paddingHorizontal: 20 },
  header: { alignItems: 'center', marginTop: 30, marginBottom: 30 },
  verdictText: { fontSize: 24, fontWeight: 'bold', marginTop: 10, letterSpacing: 1 },
  card: { backgroundColor: '#12121C', borderRadius: 16, padding: 20, borderWidth: 1, borderColor: '#1E1E30', marginBottom: 20 },
  cardLabel: { color: '#5A5A7A', fontSize: 10, fontWeight: 'bold', marginBottom: 10, textAlign: 'center' },
  probValue: { fontSize: 32, fontWeight: 'bold', textAlign: 'center', marginBottom: 10 },
  barBg: { height: 8, backgroundColor: '#1E1E30', borderRadius: 4, overflow: 'hidden' },
  barFill: { height: '100%' },
  sectionTitle: { color: '#5A5A7A', fontSize: 12, fontWeight: 'bold', marginBottom: 12, letterSpacing: 1 },
  detailRow: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 12, borderBottomWidth: 1, borderBottomColor: '#1E1E30', paddingBottom: 8 },
  detailLabel: { color: '#5A5A7A', fontSize: 14 },
  detailValue: { color: '#EAEAF5', fontSize: 14, fontWeight: '600' },
  infoBox: { flexDirection: 'row', alignItems: 'center', marginTop: 10, backgroundColor: '#0A0A0F', padding: 10, borderRadius: 8 },
  infoText: { color: '#5A5A7A', fontSize: 12, marginLeft: 8, flex: 1 },
  backBtn: { paddingVertical: 18, alignItems: 'center' },
  backBtnText: { color: '#4F6EF7', fontSize: 16, fontWeight: 'bold' }
});
