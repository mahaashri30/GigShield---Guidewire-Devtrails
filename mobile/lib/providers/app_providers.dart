import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:gigshield/services/api_service.dart';

// ── Core providers ────────────────────────────────────────────────────────────

final apiServiceProvider = Provider<ApiService>((ref) => ApiService());

// ── Auth state ────────────────────────────────────────────────────────────────

class AuthState {
  final bool isLoggedIn;
  final bool isNewUser;
  final String? workerId;
  final String? selectedPlatform;
  final bool isLoading;
  final String? error;
  const AuthState({
    this.isLoggedIn = false,
    this.isNewUser = false,
    this.workerId,
    this.selectedPlatform,
    this.isLoading = false,
    this.error,
  });
  AuthState copyWith({bool? isLoggedIn, bool? isNewUser, String? workerId, String? selectedPlatform, bool? isLoading, String? error}) =>
      AuthState(
        isLoggedIn: isLoggedIn ?? this.isLoggedIn,
        isNewUser: isNewUser ?? this.isNewUser,
        workerId: workerId ?? this.workerId,
        selectedPlatform: selectedPlatform ?? this.selectedPlatform,
        isLoading: isLoading ?? this.isLoading,
        error: error,
      );
}

class AuthNotifier extends StateNotifier<AuthState> {
  final ApiService _api;
  AuthNotifier(this._api) : super(const AuthState()) {
    _checkAuth();
  }

  Future<void> _checkAuth() async {
    final loggedIn = await _api.isLoggedIn();
    state = state.copyWith(isLoggedIn: loggedIn);
  }

  Future<Map<String, dynamic>> sendOtp(String phone) async {
    state = state.copyWith(isLoading: true, error: null);
    try {
      final res = await _api.sendOtp(phone);
      state = state.copyWith(isLoading: false);
      return res;
    } catch (e) {
      state = state.copyWith(isLoading: false, error: e.toString());
      rethrow;
    }
  }

  Future<bool> verifyOtp(String phone, String otp) async {
    state = state.copyWith(isLoading: true, error: null);
    try {
      final res = await _api.verifyOtp(phone, otp);
      await _api.saveTokens(
        res['access_token'],
        res['refresh_token'],
        res['worker_id'],
      );
      final isNew = res['is_new_user'] ?? false;
      // For new users, don't set isLoggedIn yet — wait until registration completes
      state = state.copyWith(
        isLoggedIn: !isNew,
        isNewUser: isNew,
        workerId: res['worker_id'],
        isLoading: false,
      );
      return isNew;
    } catch (e) {
      state = state.copyWith(isLoading: false, error: 'Invalid OTP. Try again.');
      return false;
    }
  }

  Future<void> completeRegistration() async {
    state = state.copyWith(isLoggedIn: true, isNewUser: false);
  }

  void setPlatform(String platform) {
    state = state.copyWith(selectedPlatform: platform);
  }

  Future<void> logout() async {
    await _api.logout();
    state = const AuthState(isNewUser: false);
  }
}

final authProvider = StateNotifierProvider<AuthNotifier, AuthState>(
  (ref) => AuthNotifier(ref.watch(apiServiceProvider)),
);

// ── Worker/Dashboard state ─────────────────────────────────────────────────────

final dashboardProvider = FutureProvider.autoDispose<Map<String, dynamic>>((ref) async {
  final api = ref.watch(apiServiceProvider);
  return api.getDashboard();
});

final activePolicyProvider = FutureProvider.autoDispose<Map<String, dynamic>?>((ref) async {
  final api = ref.watch(apiServiceProvider);
  try {
    return await api.getActivePolicy();
  } catch (_) {
    return null;
  }
});

final activeDisruptionsProvider = FutureProvider.autoDispose.family<List<dynamic>, String>(
  (ref, city) async {
    final api = ref.watch(apiServiceProvider);
    return api.getActiveDisruptions(city);
  },
);

final claimsProvider = FutureProvider.autoDispose<List<dynamic>>((ref) async {
  final api = ref.watch(apiServiceProvider);
  return api.listClaims();
});

final payoutsProvider = FutureProvider.autoDispose<List<dynamic>>((ref) async {
  final api = ref.watch(apiServiceProvider);
  return api.listPayouts();
});

// ── Premium Quote ─────────────────────────────────────────────────────────────

final premiumQuoteProvider = FutureProvider.autoDispose.family<Map<String, dynamic>, String>(
  (ref, tier) async {
    final api = ref.watch(apiServiceProvider);
    return api.getPremiumQuote(tier);
  },
);

// ── Selected tier for policy purchase ─────────────────────────────────────────

final selectedTierProvider = StateProvider<String>((ref) => 'smart');
