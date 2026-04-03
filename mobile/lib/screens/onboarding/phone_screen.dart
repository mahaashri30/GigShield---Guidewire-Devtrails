import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:video_player/video_player.dart';
import 'package:susanoo/theme/app_theme.dart';
import 'package:susanoo/providers/app_providers.dart';

class PhoneScreen extends ConsumerStatefulWidget {
  const PhoneScreen({super.key});

  @override
  ConsumerState<PhoneScreen> createState() => _PhoneScreenState();
}

class _PhoneScreenState extends ConsumerState<PhoneScreen> {
  final _phoneCtrl = TextEditingController();
  final _formKey = GlobalKey<FormState>();
  late VideoPlayerController _videoCtrl;

  @override
  void initState() {
    super.initState();
    _videoCtrl = VideoPlayerController.asset('assets/videos/naruto_bg.mp4')
      ..initialize().then((_) {
        _videoCtrl.setLooping(true);
        _videoCtrl.setVolume(0);
        _videoCtrl.play();
        if (mounted) setState(() {});
      });
  }

  @override
  void dispose() {
    _phoneCtrl.dispose();
    _videoCtrl.dispose();
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
      body: Stack(
        fit: StackFit.expand,
        children: [
          // Naruto video background
          if (_videoCtrl.value.isInitialized)
            FittedBox(
              fit: BoxFit.cover,
              child: SizedBox(
                width: _videoCtrl.value.size.width,
                height: _videoCtrl.value.size.height,
                child: VideoPlayer(_videoCtrl),
              ),
            ),

          // Dark gradient overlay
          Container(
            decoration: const BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.topCenter,
                end: Alignment.bottomCenter,
                colors: [
                  Color(0xAA000000),
                  Color(0xCC000000),
                ],
              ),
            ),
          ),

          // Content
          SafeArea(
            child: SingleChildScrollView(
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
                        color: Colors.white.withOpacity(0.15),
                        borderRadius: BorderRadius.circular(16),
                        border: Border.all(color: Colors.white.withOpacity(0.3)),
                      ),
                      child: const Icon(Icons.shield_rounded, color: Colors.white, size: 36),
                    ),
                    const SizedBox(height: 32),
                    const Text(
                      'Welcome to\nSusanoo 🛡️',
                      style: TextStyle(fontSize: 32, fontWeight: FontWeight.w800, height: 1.2, color: Colors.white),
                    ),
                    const SizedBox(height: 12),
                    Text(
                      '"The Ultimate Defense" for delivery heroes.\nEnter your mobile number to get started.',
                      style: TextStyle(fontSize: 16, color: Colors.white.withOpacity(0.8), height: 1.5),
                    ),
                    const SizedBox(height: 40),

                    // Phone input on frosted card
                    Container(
                      padding: const EdgeInsets.all(20),
                      decoration: BoxDecoration(
                        color: Colors.white.withOpacity(0.12),
                        borderRadius: BorderRadius.circular(16),
                        border: Border.all(color: Colors.white.withOpacity(0.2)),
                      ),
                      child: Column(
                        children: [
                          Theme(
                            data: Theme.of(context).copyWith(
                              inputDecorationTheme: const InputDecorationTheme(
                                filled: true,
                                fillColor: Colors.transparent,
                              ),
                            ),
                            child: TextFormField(
                            controller: _phoneCtrl,
                            keyboardType: TextInputType.phone,
                            style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w600),
                            inputFormatters: [
                              FilteringTextInputFormatter.digitsOnly,
                              LengthLimitingTextInputFormatter(10),
                            ],
                            decoration: InputDecoration(
                              prefixText: '+91  ',
                              prefixStyle: const TextStyle(fontWeight: FontWeight.w600, color: Colors.white),
                              hintText: '9876543210',
                              hintStyle: TextStyle(color: Colors.white.withOpacity(0.4)),
                              labelText: 'Mobile Number',
                              labelStyle: TextStyle(color: Colors.white.withOpacity(0.7)),
                              filled: true,
                              fillColor: Colors.white.withOpacity(0.08),
                              enabledBorder: OutlineInputBorder(
                                borderRadius: BorderRadius.circular(10),
                                borderSide: BorderSide(color: Colors.white.withOpacity(0.3)),
                              ),
                              focusedBorder: OutlineInputBorder(
                                borderRadius: BorderRadius.circular(10),
                                borderSide: const BorderSide(color: Colors.white),
                              ),
                              errorBorder: OutlineInputBorder(
                                borderRadius: BorderRadius.circular(10),
                                borderSide: BorderSide(color: AppTheme.danger),
                              ),
                              focusedErrorBorder: OutlineInputBorder(
                                borderRadius: BorderRadius.circular(10),
                                borderSide: BorderSide(color: AppTheme.danger),
                              ),
                            ),
                            validator: (v) {
                              if (v == null || v.length != 10) return 'Enter a valid 10-digit number';
                              return null;
                            },
                          ),
                          ),
                          const SizedBox(height: 16),
                          ElevatedButton(
                            onPressed: auth.isLoading ? null : _submit,
                            style: ElevatedButton.styleFrom(
                              backgroundColor: AppTheme.primary,
                              minimumSize: const Size(double.infinity, 52),
                            ),
                            child: auth.isLoading
                                ? const Row(
                                    mainAxisAlignment: MainAxisAlignment.center,
                                    children: [
                                      SizedBox(height: 20, width: 20, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2)),
                                      SizedBox(width: 12),
                                      Text('Sending OTP...', style: TextStyle(color: Colors.white)),
                                    ],
                                  )
                                : const Text('Send OTP'),
                          ),
                        ],
                      ),
                    ),

                    const SizedBox(height: 16),
                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: Colors.black.withOpacity(0.4),
                        borderRadius: BorderRadius.circular(10),
                        border: Border.all(color: const Color(0xFFFFE082).withOpacity(0.5)),
                      ),
                      child: const Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              Icon(Icons.info_outline_rounded, size: 16, color: Color(0xFFF59E0B)),
                              SizedBox(width: 6),
                              Text('How it works', style: TextStyle(fontWeight: FontWeight.w700, fontSize: 13, color: Color(0xFFFFE082))),
                            ],
                          ),
                          SizedBox(height: 8),
                          Text(
                            '• Real users: Enter your registered mobile number to receive a live OTP via SMS.',
                            style: TextStyle(fontSize: 12, color: Colors.white70, height: 1.5),
                          ),
                          Text(
                            '• Demo / Testing: Use any number and enter OTP 123456 to explore the app in demo mode.',
                            style: TextStyle(fontSize: 12, color: Colors.white70, height: 1.5),
                          ),
                        ],
                      ),
                    ),

                    if (auth.isLoading)
                      const Padding(
                        padding: EdgeInsets.only(top: 12),
                        child: Center(
                          child: Text(
                            'Please wait up to 30 seconds\nfor the server to wake up.',
                            textAlign: TextAlign.center,
                            style: TextStyle(fontSize: 12, color: Colors.white54),
                          ),
                        ),
                      ),
                    const SizedBox(height: 16),
                    Center(
                      child: Text(
                        'By continuing, you agree to our Terms & Privacy Policy',
                        style: TextStyle(fontSize: 12, color: Colors.white.withOpacity(0.4)),
                        textAlign: TextAlign.center,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
