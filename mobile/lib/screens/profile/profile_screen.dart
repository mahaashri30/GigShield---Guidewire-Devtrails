import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:susanoo/theme/app_theme.dart';
import 'package:susanoo/providers/app_providers.dart';

class ProfileScreen extends ConsumerWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final dashAsync = ref.watch(dashboardProvider);

    return Scaffold(
      backgroundColor: AppTheme.surface,
      appBar: AppBar(title: const Text('Profile'), backgroundColor: Colors.white),
      body: dashAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Text('Error: $e')),
        data: (data) {
          final worker = data['worker'] as Map<String, dynamic>? ?? {};
          final name = worker['name'] as String? ?? 'Rider';
          final phone = worker['phone'] as String? ?? '';
          final city = worker['city'] as String? ?? '';
          final platform = (worker['platform'] as String?)?.toUpperCase() ?? '';
          final upi = worker['upi_id'] as String? ?? 'Not set';
          final avgEarnings = (worker['avg_daily_earnings'] as num?)?.toStringAsFixed(0) ?? '600';
          final riskScore = ((worker['risk_score'] as num?)?.toDouble() ?? 0.5) * 100;

          return SingleChildScrollView(
            padding: const EdgeInsets.all(20),
            child: Column(
              children: [
                // Avatar
                Container(
                  width: 80,
                  height: 80,
                  decoration: BoxDecoration(
                    color: AppTheme.primaryLight,
                    shape: BoxShape.circle,
                  ),
                  child: Center(
                    child: Text(
                      name.isNotEmpty ? name[0].toUpperCase() : 'R',
                      style: const TextStyle(fontSize: 36, fontWeight: FontWeight.w700, color: AppTheme.primary),
                    ),
                  ),
                ),
                const SizedBox(height: 12),
                Text(name, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w700)),
                Text('$platform • $city', style: const TextStyle(color: AppTheme.textSecondary)),
                const SizedBox(height: 24),

                // Info section
                _Section(title: 'Account Details', tiles: [
                  _Tile(icon: Icons.phone, label: 'Mobile', value: phone),
                  _Tile(icon: Icons.account_balance_wallet_outlined, label: 'UPI ID', value: upi),
                  _Tile(icon: Icons.location_city, label: 'City', value: city),
                ]),

                const SizedBox(height: 16),

                _Section(title: 'Risk Profile', tiles: [
                  _Tile(icon: Icons.bar_chart, label: 'Avg Daily Earnings', value: '₹$avgEarnings'),
                  _Tile(icon: Icons.security, label: 'Risk Score', value: '${riskScore.toInt()}/100'),
                ]),

                const SizedBox(height: 24),

                OutlinedButton.icon(
                  onPressed: () async {
                    await ref.read(authProvider.notifier).logout();
                    if (context.mounted) context.go('/auth/phone');
                  },
                  icon: const Icon(Icons.logout, color: AppTheme.danger),
                  label: const Text('Logout', style: TextStyle(color: AppTheme.danger)),
                  style: OutlinedButton.styleFrom(side: const BorderSide(color: AppTheme.danger)),
                ),
              ],
            ),
          );
        },
      ),
    );
  }
}

class _Section extends StatelessWidget {
  final String title;
  final List<Widget> tiles;
  const _Section({required this.title, required this.tiles});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(title, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 15)),
        const SizedBox(height: 8),
        Container(
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: AppTheme.divider, width: 0.5),
          ),
          child: Column(children: tiles),
        ),
      ],
    );
  }
}

class _Tile extends StatelessWidget {
  final IconData icon;
  final String label, value;
  const _Tile({required this.icon, required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      child: Row(
        children: [
          Icon(icon, size: 20, color: AppTheme.textSecondary),
          const SizedBox(width: 12),
          Text(label, style: const TextStyle(color: AppTheme.textSecondary, fontSize: 14)),
          const Spacer(),
          Text(value, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14)),
        ],
      ),
    );
  }
}
