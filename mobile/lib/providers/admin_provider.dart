import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:susanoo/utils/constants.dart';
import 'package:dio/dio.dart';

class AdminAuthState {
  final bool isLoggedIn;
  final bool isLoading;
  final String? error;
  const AdminAuthState({
    this.isLoggedIn = false,
    this.isLoading = false,
    this.error,
  });
  AdminAuthState copyWith({bool? isLoggedIn, bool? isLoading, String? error}) =>
      AdminAuthState(
        isLoggedIn: isLoggedIn ?? this.isLoggedIn,
        isLoading: isLoading ?? this.isLoading,
        error: error,
      );
}

class AdminAuthNotifier extends StateNotifier<AdminAuthState> {
  static const _storage = FlutterSecureStorage(
    aOptions: AndroidOptions(encryptedSharedPreferences: true),
  );
  static const _kAdminKey = 'admin_api_key';

  AdminAuthNotifier() : super(const AdminAuthState()) {
    _checkStored();
  }

  Future<void> _checkStored() async {
    final key = await _storage.read(key: _kAdminKey);
    if (key != null && key.isNotEmpty) {
      state = state.copyWith(isLoggedIn: true);
    }
  }

  Future<String?> getStoredKey() => _storage.read(key: _kAdminKey);

  /// Validates the admin API key against the backend /admin/stats endpoint.
  Future<void> login(String apiKey) async {
    state = state.copyWith(isLoading: true, error: null);
    try {
      final dio = Dio(BaseOptions(
        baseUrl: AppConstants.baseUrl,
        connectTimeout: const Duration(seconds: 10),
        receiveTimeout: const Duration(seconds: 15),
      ));
      await dio.get(
        '/admin/stats',
        options: Options(headers: {'X-Admin-API-Key': apiKey}),
      );
      await _storage.write(key: _kAdminKey, value: apiKey);
      state = state.copyWith(isLoggedIn: true, isLoading: false);
    } on DioException catch (e) {
      final msg = e.response?.statusCode == 403
          ? 'Invalid admin credentials'
          : 'Cannot reach server. Check your connection.';
      state = state.copyWith(isLoading: false, error: msg);
    } catch (e) {
      state = state.copyWith(isLoading: false, error: e.toString());
    }
  }

  Future<void> logout() async {
    await _storage.delete(key: _kAdminKey);
    state = const AdminAuthState();
  }
}

final adminAuthProvider =
    StateNotifierProvider<AdminAuthNotifier, AdminAuthState>(
  (_) => AdminAuthNotifier(),
);

/// Provides a Dio instance pre-configured with the stored admin API key.
final adminDioProvider = FutureProvider<Dio>((ref) async {
  const storage = FlutterSecureStorage(
    aOptions: AndroidOptions(encryptedSharedPreferences: true),
  );
  final key = await storage.read(key: 'admin_api_key') ?? '';
  final dio = Dio(BaseOptions(
    baseUrl: AppConstants.baseUrl,
    connectTimeout: const Duration(seconds: 10),
    receiveTimeout: const Duration(seconds: 20),
    headers: {
      'Content-Type': 'application/json',
      if (key.isNotEmpty) 'X-Admin-API-Key': key,
    },
  ));
  return dio;
});

/// Admin stats — fetched from /admin/stats
final adminStatsProvider = FutureProvider.autoDispose<Map<String, dynamic>>((ref) async {
  final dioPod = await ref.watch(adminDioProvider.future);
  final res = await dioPod.get('/admin/stats');
  return res.data as Map<String, dynamic>;
});

/// Admin claims list
final adminClaimsProvider = FutureProvider.autoDispose<List<dynamic>>((ref) async {
  final dioPod = await ref.watch(adminDioProvider.future);
  final res = await dioPod.get('/admin/claims');
  return res.data as List<dynamic>;
});

/// Admin workers list
final adminWorkersProvider = FutureProvider.autoDispose<List<dynamic>>((ref) async {
  final dioPod = await ref.watch(adminDioProvider.future);
  final res = await dioPod.get('/admin/workers');
  return res.data as List<dynamic>;
});

/// Admin disruptions list
final adminDisruptionsProvider = FutureProvider.autoDispose<List<dynamic>>((ref) async {
  final dioPod = await ref.watch(adminDioProvider.future);
  final res = await dioPod.get('/admin/disruptions');
  return res.data as List<dynamic>;
});

/// Disbursement ratio
final adminDisbursementProvider = FutureProvider.autoDispose<Map<String, dynamic>>((ref) async {
  final dioPod = await ref.watch(adminDioProvider.future);
  final res = await dioPod.get('/admin/disbursement-ratio');
  return res.data as Map<String, dynamic>;
});

/// Analytics
final adminAnalyticsProvider = FutureProvider.autoDispose<Map<String, dynamic>>((ref) async {
  final dioPod = await ref.watch(adminDioProvider.future);
  final res = await dioPod.get('/admin/analytics');
  return res.data as Map<String, dynamic>;
});
