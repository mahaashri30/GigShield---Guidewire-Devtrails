import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:gigshield/providers/app_providers.dart';
import 'package:gigshield/screens/splash_screen.dart';
import 'package:gigshield/screens/onboarding/phone_screen.dart';
import 'package:gigshield/screens/onboarding/otp_screen.dart';
import 'package:gigshield/screens/onboarding/register_screen.dart';
import 'package:gigshield/screens/home/home_screen.dart';
import 'package:gigshield/screens/policy/policy_screen.dart';
import 'package:gigshield/screens/policy/buy_policy_screen.dart';
import 'package:gigshield/screens/claims/claims_screen.dart';
import 'package:gigshield/screens/profile/profile_screen.dart';
import 'package:gigshield/screens/shell_screen.dart';

// Bridges Riverpod state changes into a Listenable that GoRouter can watch
class _AuthListenable extends ChangeNotifier {
  _AuthListenable(this._ref) {
    _ref.listen<AuthState>(authProvider, (_, __) => notifyListeners());
  }
  final Ref _ref;
  bool get isLoggedIn => _ref.read(authProvider).isLoggedIn;
}

final appRouterProvider = Provider<GoRouter>((ref) {
  final listenable = _AuthListenable(ref);

  return GoRouter(
    initialLocation: '/splash',
    refreshListenable: listenable,
    redirect: (context, state) {
      final isLoggedIn = listenable.isLoggedIn;
      final onAuth = state.matchedLocation.startsWith('/auth');
      final onSplash = state.matchedLocation == '/splash';
      final onRegister = state.matchedLocation == '/auth/register';

      if (onSplash) return null;
      if (onRegister) return null;
      if (!isLoggedIn && !onAuth) return '/auth/phone';
      if (isLoggedIn && onAuth) return '/home';
      return null;
    },
    routes: [
      GoRoute(path: '/splash', builder: (_, __) => const SplashScreen()),
      GoRoute(
        path: '/auth/phone',
        builder: (_, __) => const PhoneScreen(),
      ),
      GoRoute(
        path: '/auth/otp',
        builder: (context, state) {
          final phone = state.extra as String? ?? '';
          return OtpScreen(phone: phone);
        },
      ),
      GoRoute(
        path: '/auth/register',
        builder: (_, __) => const RegisterScreen(),
      ),
      ShellRoute(
        builder: (context, state, child) => ShellScreen(child: child),
        routes: [
          GoRoute(path: '/home', builder: (_, __) => const HomeScreen()),
          GoRoute(path: '/policy', builder: (_, __) => const PolicyScreen()),
          GoRoute(path: '/policy/buy', builder: (_, __) => const BuyPolicyScreen()),
          GoRoute(path: '/claims', builder: (_, __) => const ClaimsScreen()),
          GoRoute(path: '/profile', builder: (_, __) => const ProfileScreen()),
        ],
      ),
    ],
  );
});
