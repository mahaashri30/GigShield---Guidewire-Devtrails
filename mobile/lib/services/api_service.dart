import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:gigshield/utils/constants.dart';

class ApiService {
  late final Dio _dio;
  final _storage = const FlutterSecureStorage();

  ApiService() {
    _dio = Dio(BaseOptions(
      baseUrl: AppConstants.baseUrl,
      connectTimeout: const Duration(seconds: 10),
      receiveTimeout: const Duration(seconds: 15),
      headers: {'Content-Type': 'application/json'},
    ));

    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) async {
        final token = await _storage.read(key: AppConstants.accessTokenKey);
        if (token != null) {
          options.headers['Authorization'] = 'Bearer $token';
        }
        return handler.next(options);
      },
      onError: (DioException e, handler) {
        return handler.next(e);
      },
    ));
  }

  // ── Auth ──────────────────────────────────────────────────────────────────

  Future<Map<String, dynamic>> sendOtp(String phone) async {
    final res = await _dio.post('/auth/send-otp', data: {'phone': phone});
    return res.data;
  }

  Future<Map<String, dynamic>> verifyOtp(String phone, String otp) async {
    final res = await _dio.post('/auth/verify-otp', data: {'phone': phone, 'otp': otp});
    return res.data;
  }

  Future<void> saveTokens(String access, String refresh, String workerId) async {
    await _storage.write(key: AppConstants.accessTokenKey, value: access);
    await _storage.write(key: AppConstants.refreshTokenKey, value: refresh);
    await _storage.write(key: AppConstants.workerIdKey, value: workerId);
  }

  Future<bool> isLoggedIn() async {
    final token = await _storage.read(key: AppConstants.accessTokenKey);
    return token != null;
  }

  Future<void> logout() async {
    await _storage.deleteAll();
  }

  // ── Worker ────────────────────────────────────────────────────────────────

  Future<Map<String, dynamic>> registerWorker(Map<String, dynamic> data) async {
    final res = await _dio.post('/workers/register', data: data);
    return res.data;
  }

  Future<Map<String, dynamic>> getMe() async {
    final res = await _dio.get('/workers/me');
    return res.data;
  }

  Future<Map<String, dynamic>> getDashboard() async {
    final res = await _dio.get('/workers/dashboard');
    return res.data;
  }

  // ── Policies ──────────────────────────────────────────────────────────────

  Future<Map<String, dynamic>> getPremiumQuote(String tier) async {
    final res = await _dio.get('/policies/quote', queryParameters: {'tier': tier});
    return res.data;
  }

  Future<Map<String, dynamic>> createPolicyOrder(String tier) async {
    final res = await _dio.post('/policies/create-order', data: {'tier': tier});
    return res.data;
  }

  Future<Map<String, dynamic>> verifyPolicyPayment(Map<String, dynamic> data) async {
    final res = await _dio.post('/policies/verify-payment', data: data);
    return res.data;
  }

  Future<Map<String, dynamic>> createPolicy(String tier) async {
    final res = await _dio.post('/policies/', data: {'tier': tier});
    return res.data;
  }

  Future<Map<String, dynamic>> getActivePolicy() async {
    final res = await _dio.get('/policies/active');
    return res.data;
  }

  Future<List<dynamic>> listPolicies() async {
    final res = await _dio.get('/policies/');
    return res.data;
  }

  // ── Disruptions ───────────────────────────────────────────────────────────

  Future<List<dynamic>> getActiveDisruptions(String city) async {
    final res = await _dio.get('/disruptions/active', queryParameters: {'city': city});
    return res.data;
  }

  Future<List<dynamic>> simulateDisruption(String city, String pincode) async {
    final res = await _dio.post(
      '/disruptions/simulate',
      queryParameters: {'city': city, 'pincode': pincode},
    );
    return res.data;
  }

  // ── Claims ────────────────────────────────────────────────────────────────

  Future<Map<String, dynamic>> triggerClaim(String disruptionEventId) async {
    final res = await _dio.post('/claims/trigger/$disruptionEventId');
    return res.data;
  }

  Future<List<dynamic>> listClaims() async {
    final res = await _dio.get('/claims/');
    return res.data;
  }

  // ── Payouts ───────────────────────────────────────────────────────────────

  Future<List<dynamic>> listPayouts() async {
    final res = await _dio.get('/payouts/');
    return res.data;
  }
}
