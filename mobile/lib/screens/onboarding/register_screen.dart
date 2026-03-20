import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:gigshield/theme/app_theme.dart';
import 'package:gigshield/providers/app_providers.dart';
import 'package:gigshield/utils/constants.dart';

class RegisterScreen extends ConsumerStatefulWidget {
  const RegisterScreen({super.key});

  @override
  ConsumerState<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends ConsumerState<RegisterScreen> {
  final _nameCtrl = TextEditingController();
  final _upiCtrl  = TextEditingController();
  final _formKey  = GlobalKey<FormState>();

  String _selectedPlatform = 'blinkit';
  String _selectedCity     = 'Bangalore';
  String _pincode          = '560001';
  bool   _loading          = false;

  // Platform earnings fetched automatically
  Map<String, dynamic>? _platformEarnings;
  bool _fetchingEarnings = false;

  final Map<String, String> _cityPincode = {
    'Bangalore': '560001',
    'Mumbai':    '400001',
    'Delhi':     '110001',
    'Chennai':   '600001',
    'Hyderabad': '500001',
    'Pune':      '411001',
    'Kolkata':   '700001',
  };

  @override
  void initState() {
    super.initState();
    // Fetch earnings for default platform on load
    WidgetsBinding.instance.addPostFrameCallback((_) => _fetchEarnings(_selectedPlatform));
  }

  @override
  void dispose() {
    _nameCtrl.dispose();
    _upiCtrl.dispose();
    super.dispose();
  }

  Future<void> _fetchEarnings(String platform) async {
    setState(() { _fetchingEarnings = true; _platformEarnings = null; });
    try {
      final data = await ref.read(apiServiceProvider).getPlatformEarnings(platform);
      if (mounted) setState(() => _platformEarnings = data);
    } catch (_) {
      // Non-fatal — registration still works, backend uses default
    } finally {
      if (mounted) setState(() => _fetchingEarnings = false);
    }
  }

  void _submit() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _loading = true);
    try {
      await ref.read(apiServiceProvider).registerWorker({
        'phone': '',
        'name': _nameCtrl.text.trim(),
        'platform': _selectedPlatform,
        'city': _selectedCity,
        'pincode': _pincode,
        'upi_id': _upiCtrl.text.trim().isEmpty ? null : _upiCtrl.text.trim(),
        // avg_daily_earnings is set server-side from platform API — not sent by client
      });
      await ref.read(authProvider.notifier).completeRegistration();
      if (mounted) context.go('/home');
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error: $e'), backgroundColor: AppTheme.danger),
        );
      }
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Complete Profile')),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('Tell us about yourself', style: TextStyle(fontSize: 22, fontWeight: FontWeight.w700)),
                const SizedBox(height: 6),
                const Text('This helps us calculate your personalised premium', style: TextStyle(color: AppTheme.textSecondary)),
                const SizedBox(height: 32),

                // Name
                const Text('Full Name', style: TextStyle(fontWeight: FontWeight.w600, fontSize: 14)),
                const SizedBox(height: 8),
                TextFormField(
                  controller: _nameCtrl,
                  decoration: const InputDecoration(hintText: 'Ravi Kumar'),
                  validator: (v) => v == null || v.isEmpty ? 'Enter your name' : null,
                ),
                const SizedBox(height: 20),

                // Platform
                const Text('Delivery Platform', style: TextStyle(fontWeight: FontWeight.w600, fontSize: 14)),
                const SizedBox(height: 8),
                Wrap(
                  spacing: 8, runSpacing: 8,
                  children: AppConstants.platforms.map((p) {
                    final selected = _selectedPlatform == p['value'];
                    return GestureDetector(
                      onTap: () {
                        setState(() => _selectedPlatform = p['value']!);
                        _fetchEarnings(p['value']!);
                      },
                      child: AnimatedContainer(
                        duration: const Duration(milliseconds: 200),
                        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                        decoration: BoxDecoration(
                          color: selected ? AppTheme.primary : Colors.white,
                          border: Border.all(color: selected ? AppTheme.primary : AppTheme.divider),
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: Text(
                          p['label']!,
                          style: TextStyle(
                            color: selected ? Colors.white : AppTheme.textPrimary,
                            fontWeight: FontWeight.w600,
                            fontSize: 14,
                          ),
                        ),
                      ),
                    );
                  }).toList(),
                ),
                const SizedBox(height: 16),

                // Platform earnings card — auto-fetched, no user input
                _EarningsCard(
                  earnings: _platformEarnings,
                  loading: _fetchingEarnings,
                  platform: _selectedPlatform,
                ),
                const SizedBox(height: 20),

                // City
                const Text('Your City', style: TextStyle(fontWeight: FontWeight.w600, fontSize: 14)),
                const SizedBox(height: 8),
                DropdownButtonFormField<String>(
                  value: _selectedCity,
                  decoration: const InputDecoration(hintText: 'Select city'),
                  items: AppConstants.supportedCities
                      .map((c) => DropdownMenuItem(value: c, child: Text(c)))
                      .toList(),
                  onChanged: (v) {
                    setState(() {
                      _selectedCity = v!;
                      _pincode = _cityPincode[v] ?? '560001';
                    });
                  },
                ),
                const SizedBox(height: 20),

                // UPI (optional)
                const Text('UPI ID (for payouts)', style: TextStyle(fontWeight: FontWeight.w600, fontSize: 14)),
                const SizedBox(height: 8),
                TextFormField(
                  controller: _upiCtrl,
                  decoration: const InputDecoration(
                    hintText: 'ravi@upi (optional)',
                    suffixIcon: Icon(Icons.account_balance_wallet_outlined),
                  ),
                ),
                const SizedBox(height: 6),
                const Text(
                  '💡 Claims will be paid directly to your UPI account within minutes',
                  style: TextStyle(fontSize: 12, color: AppTheme.textSecondary),
                ),

                const SizedBox(height: 40),
                ElevatedButton(
                  onPressed: _loading ? null : _submit,
                  child: _loading
                      ? const SizedBox(height: 20, width: 20, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                      : const Text('Complete Registration'),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _EarningsCard extends StatelessWidget {
  final Map<String, dynamic>? earnings;
  final bool loading;
  final String platform;
  const _EarningsCard({required this.earnings, required this.loading, required this.platform});

  @override
  Widget build(BuildContext context) {
    if (loading) {
      return Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: AppTheme.primaryLight,
          borderRadius: BorderRadius.circular(12),
        ),
        child: const Row(
          children: [
            SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2)),
            SizedBox(width: 12),
            Text('Fetching your earnings from platform...', style: TextStyle(fontSize: 13, color: AppTheme.primary)),
          ],
        ),
      );
    }

    if (earnings == null) return const SizedBox.shrink();

    final avg    = (earnings!['avg_daily_earnings'] as num?)?.toStringAsFixed(0) ?? '—';
    final weekly = (earnings!['weekly_settlement']  as num?)?.toStringAsFixed(0) ?? '—';
    final days   = earnings!['active_days_last_week'] ?? '—';
    final source = earnings!['source'] as String? ?? '';
    final verified = earnings!['verified'] as bool? ?? false;

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFFF0FDF4),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppTheme.success.withOpacity(0.3)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(verified ? Icons.verified_rounded : Icons.info_outline_rounded,
                  color: verified ? AppTheme.success : AppTheme.warning, size: 16),
              const SizedBox(width: 6),
              Expanded(
                child: Text(
                  verified ? 'Earnings verified from $source' : 'Using estimated earnings',
                  style: TextStyle(
                    fontSize: 12,
                    color: verified ? AppTheme.success : AppTheme.warning,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              _Stat('Avg Daily', '₹$avg'),
              _Stat('Last Week', '₹$weekly'),
              _Stat('Active Days', '$days days'),
            ],
          ),
          const SizedBox(height: 8),
          const Text(
            'Your payout will compensate the income you lose on disruption days.',
            style: TextStyle(fontSize: 11, color: AppTheme.textSecondary),
          ),
        ],
      ),
    );
  }
}

class _Stat extends StatelessWidget {
  final String label, value;
  const _Stat(this.label, this.value);

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(value, style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 16)),
        Text(label, style: const TextStyle(fontSize: 11, color: AppTheme.textSecondary)),
      ],
    );
  }
}
