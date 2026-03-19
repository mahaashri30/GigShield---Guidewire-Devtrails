import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:gigshield/theme/app_theme.dart';
import 'package:gigshield/providers/app_providers.dart';

class PhoneScreen extends ConsumerStatefulWidget {
  const PhoneScreen({super.key});

  @override
  ConsumerState<PhoneScreen> createState() => _PhoneScreenState();
}

class _PhoneScreenState extends ConsumerState<PhoneScreen> {
  final _phoneCtrl = TextEditingController();
  final _formKey = GlobalKey<FormState>();

  @override
  void dispose() {
    _phoneCtrl.dispose();
    super.dispose();
  }

  void _submit() async {
    if (!_formKey.currentState!.validate()) return;
    final phone = '+91${_phoneCtrl.text.trim()}';
    try {
      await ref.read(authProvider.notifier).sendOtp(phone);
      if (mounted) context.push('/auth/otp', extra: phone);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error: $e'), backgroundColor: AppTheme.danger),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final auth = ref.watch(authProvider);

    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const SizedBox(height: 40),
                Container(
                  width: 64,
                  height: 64,
                  decoration: BoxDecoration(
                    color: AppTheme.primaryLight,
                    borderRadius: BorderRadius.circular(16),
                  ),
                  child: const Icon(Icons.shield_rounded, color: AppTheme.primary, size: 36),
                ),
                const SizedBox(height: 32),
                const Text(
                  'Welcome to\nGigShield 👋',
                  style: TextStyle(fontSize: 32, fontWeight: FontWeight.w800, height: 1.2),
                ),
                const SizedBox(height: 12),
                Text(
                  'Income protection for delivery heroes.\nEnter your mobile number to get started.',
                  style: TextStyle(fontSize: 16, color: AppTheme.textSecondary, height: 1.5),
                ),
                const SizedBox(height: 40),
                TextFormField(
                  controller: _phoneCtrl,
                  keyboardType: TextInputType.phone,
                  inputFormatters: [FilteringTextInputFormatter.digitsOnly, LengthLimitingTextInputFormatter(10)],
                  decoration: const InputDecoration(
                    prefixText: '+91  ',
                    prefixStyle: TextStyle(fontWeight: FontWeight.w600, color: AppTheme.textPrimary),
                    hintText: '9876543210',
                    labelText: 'Mobile Number',
                  ),
                  validator: (v) {
                    if (v == null || v.length != 10) return 'Enter a valid 10-digit number';
                    return null;
                  },
                ),
                const Spacer(),
                ElevatedButton(
                  onPressed: auth.isLoading ? null : _submit,
                  child: auth.isLoading
                      ? const SizedBox(height: 20, width: 20, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                      : const Text('Send OTP'),
                ),
                const SizedBox(height: 16),
                Center(
                  child: Text(
                    'By continuing, you agree to our Terms & Privacy Policy',
                    style: TextStyle(fontSize: 12, color: AppTheme.textHint),
                    textAlign: TextAlign.center,
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
