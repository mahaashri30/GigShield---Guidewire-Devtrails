import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:pinput/pinput.dart';
import 'package:gigshield/theme/app_theme.dart';
import 'package:gigshield/providers/app_providers.dart';
import 'dart:async';

class OtpScreen extends ConsumerStatefulWidget {
  final String phone;
  const OtpScreen({super.key, required this.phone});

  @override
  ConsumerState<OtpScreen> createState() => _OtpScreenState();
}

class _OtpScreenState extends ConsumerState<OtpScreen> {
  final _otpCtrl = TextEditingController();
  int _resendSeconds = 30;
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    _startTimer();
  }

  void _startTimer() {
    _timer = Timer.periodic(const Duration(seconds: 1), (t) {
      if (_resendSeconds == 0) {
        t.cancel();
      } else {
        setState(() => _resendSeconds--);
      }
    });
  }

  @override
  void dispose() {
    _timer?.cancel();
    _otpCtrl.dispose();
    super.dispose();
  }

  void _verify(String otp) async {
    if (otp.length != 6) return;
    final isNew = await ref.read(authProvider.notifier).verifyOtp(widget.phone, otp);
    if (!mounted) return;
    if (ref.read(authProvider).error != null) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(ref.read(authProvider).error!), backgroundColor: AppTheme.danger),
      );
      return;
    }
    context.go(isNew ? '/auth/register' : '/home');
  }

  @override
  Widget build(BuildContext context) {
    final auth = ref.watch(authProvider);
    final defaultPinTheme = PinTheme(
      width: 56,
      height: 60,
      textStyle: const TextStyle(fontSize: 22, fontWeight: FontWeight.w700, color: AppTheme.textPrimary),
      decoration: BoxDecoration(
        color: Colors.white,
        border: Border.all(color: AppTheme.divider),
        borderRadius: BorderRadius.circular(12),
      ),
    );

    return Scaffold(
      appBar: AppBar(leading: BackButton(onPressed: () => context.pop())),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SizedBox(height: 24),
              const Text('Enter OTP', style: TextStyle(fontSize: 28, fontWeight: FontWeight.w800)),
              const SizedBox(height: 8),
              RichText(
                text: TextSpan(
                  style: const TextStyle(fontSize: 16, color: AppTheme.textSecondary),
                  children: [
                    const TextSpan(text: 'We sent a 6-digit code to\n'),
                    TextSpan(
                      text: widget.phone,
                      style: const TextStyle(fontWeight: FontWeight.w700, color: AppTheme.textPrimary),
                    ),
                  ],
                ),
              ),
              Container(
                margin: const EdgeInsets.symmetric(vertical: 8),
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: AppTheme.primaryLight,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: const Text(
                  '🧪 Dev mode: OTP is 123456',
                  style: TextStyle(color: AppTheme.primary, fontWeight: FontWeight.w500, fontSize: 13),
                ),
              ),
              const SizedBox(height: 32),
              Pinput(
                controller: _otpCtrl,
                length: 6,
                defaultPinTheme: defaultPinTheme,
                focusedPinTheme: defaultPinTheme.copyDecorationWith(
                  border: Border.all(color: AppTheme.primary, width: 2),
                ),
                onCompleted: _verify,
                autofocus: true,
              ),
              const SizedBox(height: 24),
              if (auth.isLoading)
                const Center(child: CircularProgressIndicator()),
              const SizedBox(height: 16),
              Center(
                child: _resendSeconds > 0
                    ? Text(
                        'Resend OTP in $_resendSeconds s',
                        style: const TextStyle(color: AppTheme.textSecondary),
                      )
                    : TextButton(
                        onPressed: () {
                          setState(() => _resendSeconds = 30);
                          _startTimer();
                          ref.read(authProvider.notifier).sendOtp(widget.phone);
                        },
                        child: const Text('Resend OTP'),
                      ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
