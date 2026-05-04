import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:video_player/video_player.dart';
import 'package:susanoo/l10n/app_strings.dart';
import 'package:susanoo/providers/locale_provider.dart';
import 'package:susanoo/theme/app_theme.dart';
import 'package:susanoo/providers/app_providers.dart';

class PhoneScreen extends ConsumerStatefulWidget {
  const PhoneScreen({super.key});

  @override
  ConsumerState<PhoneScreen> createState() => _PhoneScreenState();
}

class _PhoneScreenState extends ConsumerState<PhoneScreen> {
  final _phoneCtrl = TextEditingController();
  final _emailCtrl = TextEditingController();
  final _passCtrl = TextEditingController();
  final _formKey = GlobalKey<FormState>();
  late VideoPlayerController _videoCtrl;
  bool _isAdminMode = false;
  bool _sending = false;

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
    _emailCtrl.dispose();
    _passCtrl.dispose();
    _videoCtrl.dispose();
    super.dispose();
  }

  void _submit() async {
    if (!_formKey.currentState!.validate()) return;
    if (_sending) return;
    setState(() => _sending = true);

    try {
      if (_isAdminMode) {
        await ref.read(authProvider.notifier).adminLogin(
              _emailCtrl.text.trim(),
              _passCtrl.text,
            );
        if (mounted) context.go('/admin/dashboard');
        return;
      }

      final phone = '+91${_phoneCtrl.text.trim()}';
      await ref.read(authProvider.notifier).sendOtp(phone);
      if (mounted) {
        context.push('/auth/otp', extra: {
          'phone': phone,
          'asAdmin': false,
        });
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(_isAdminMode ? 'Admin Login Failed: $e' : 'Error: $e'),
            backgroundColor: AppTheme.danger,
            behavior: SnackBarBehavior.floating,
          ),
        );
      }
    } finally {
      if (mounted) setState(() => _sending = false);
    }
  }

  InputDecoration _inputDeco(String label, IconData icon, {String? prefix}) {
    return InputDecoration(
      prefixText: prefix,
      prefixStyle:
          const TextStyle(color: Colors.white, fontWeight: FontWeight.w700),
      labelText: label,
      labelStyle:
          TextStyle(color: Colors.white.withOpacity(0.5), fontSize: 14),
      prefixIcon: Icon(icon, color: Colors.white, size: 20),
      filled: true,
      fillColor: Colors.white.withOpacity(0.05),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(16),
        borderSide: BorderSide(color: Colors.white.withOpacity(0.1)),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(16),
        borderSide: const BorderSide(color: Colors.white, width: 2),
      ),
      errorBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(16),
        borderSide: BorderSide(color: AppTheme.danger.withOpacity(0.5)),
      ),
      focusedErrorBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(16),
        borderSide: BorderSide(color: AppTheme.danger),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final auth = ref.watch(authProvider);
    final s = ref.watch(stringsProvider);
    final currentLang = ref.watch(localeProvider);

    return Scaffold(
      body: Stack(
        fit: StackFit.expand,
        children: [
          // Video background
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
            decoration: BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.topCenter,
                end: Alignment.bottomCenter,
                colors: [
                  Colors.black.withOpacity(0.4),
                  Colors.black.withOpacity(0.8),
                  Colors.black,
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
                    // Top bar: admin toggle + language pills
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        _AdminToggleButton(
                          isAdmin: _isAdminMode,
                          onToggle: () =>
                              setState(() => _isAdminMode = !_isAdminMode),
                        ),
                        Row(
                          children: AppStrings.all.entries.map((entry) {
                            final isSelected = entry.key == currentLang;
                            return GestureDetector(
                              onTap: () => ref
                                  .read(localeProvider.notifier)
                                  .setLanguage(entry.key),
                              child: AnimatedContainer(
                                duration: const Duration(milliseconds: 200),
                                margin: const EdgeInsets.only(left: 6),
                                padding: const EdgeInsets.symmetric(
                                    horizontal: 10, vertical: 5),
                                decoration: BoxDecoration(
                                  color: isSelected
                                      ? Colors.white
                                      : Colors.white.withOpacity(0.1),
                                  borderRadius: BorderRadius.circular(20),
                                  border: Border.all(
                                    color: isSelected
                                        ? Colors.white
                                        : Colors.white.withOpacity(0.2),
                                  ),
                                ),
                                child: Text(
                                  entry.value.languageName,
                                  style: TextStyle(
                                    fontSize: 11,
                                    fontWeight: isSelected
                                        ? FontWeight.w700
                                        : FontWeight.w400,
                                    color: isSelected
                                        ? AppTheme.primary
                                        : Colors.white,
                                  ),
                                ),
                              ),
                            );
                          }).toList(),
                        ),
                      ],
                    ),

                    const SizedBox(height: 40),

                    // Logo / icon
                    Center(
                      child: AnimatedContainer(
                        duration: const Duration(milliseconds: 400),
                        width: _isAdminMode ? 100 : 80,
                        height: _isAdminMode ? 100 : 80,
                        decoration: BoxDecoration(
                          color: Colors.white.withOpacity(0.1),
                          shape: BoxShape.circle,
                          border: Border.all(
                              color: Colors.white.withOpacity(0.2), width: 2),
                          image: _isAdminMode
                              ? const DecorationImage(
                                  image: AssetImage(
                                      'assets/images/susanoo_icon.jpg'),
                                  fit: BoxFit.cover)
                              : null,
                          boxShadow: [
                            BoxShadow(
                              color: AppTheme.primary.withOpacity(0.3),
                              blurRadius: 20,
                              spreadRadius: 5,
                            )
                          ],
                        ),
                        child: !_isAdminMode
                            ? const Icon(Icons.shield_rounded,
                                color: Colors.white, size: 40)
                            : null,
                      ),
                    ),

                    const SizedBox(height: 32),

                    // Title
                    Center(
                      child: Column(
                        children: [
                          Text(
                            _isAdminMode ? 'ADMIN PORTAL' : 'SUSANOO',
                            style: const TextStyle(
                                fontSize: 36,
                                letterSpacing: 4,
                                fontWeight: FontWeight.w900,
                                color: Colors.white),
                          ),
                          const SizedBox(height: 8),
                          Text(
                            _isAdminMode
                                ? 'Management & Oversight'
                                : 'The Ultimate Defense',
                            style: TextStyle(
                                fontSize: 14,
                                letterSpacing: 2,
                                fontWeight: FontWeight.w500,
                                color: Colors.white.withOpacity(0.6)),
                          ),
                        ],
                      ),
                    ),

                    const SizedBox(height: 60),

                    // Input card with glassmorphism
                    AnimatedSize(
                      duration: const Duration(milliseconds: 300),
                      child: ClipRRect(
                        borderRadius: BorderRadius.circular(24),
                        child: BackdropFilter(
                          filter:
                              ImageFilter.blur(sigmaX: 10, sigmaY: 10),
                          child: Container(
                            padding: const EdgeInsets.all(24),
                            decoration: BoxDecoration(
                              color: Colors.white.withOpacity(0.08),
                              borderRadius: BorderRadius.circular(24),
                              border: Border.all(
                                  color: Colors.white.withOpacity(0.15)),
                            ),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  _isAdminMode
                                      ? 'System Login'
                                      : s.mobileNumber,
                                  style: const TextStyle(
                                    color: Colors.white,
                                    fontWeight: FontWeight.w700,
                                    fontSize: 18,
                                  ),
                                ),
                                const SizedBox(height: 20),
                                if (!_isAdminMode)
                                  TextFormField(
                                    controller: _phoneCtrl,
                                    keyboardType: TextInputType.phone,
                                    style: const TextStyle(
                                        color: Colors.white,
                                        fontSize: 18,
                                        fontWeight: FontWeight.w600),
                                    inputFormatters: [
                                      FilteringTextInputFormatter.digitsOnly,
                                      LengthLimitingTextInputFormatter(10),
                                    ],
                                    decoration: _inputDeco(s.mobileNumber,
                                        Icons.phone_android_rounded,
                                        prefix: '+91 '),
                                    validator: (v) {
                                      if (_isAdminMode) return null;
                                      if (v == null || v.length != 10)
                                        return s.invalidPhone;
                                      return null;
                                    },
                                  )
                                else ...[
                                  TextFormField(
                                    controller: _emailCtrl,
                                    keyboardType: TextInputType.emailAddress,
                                    style: const TextStyle(
                                        color: Colors.white,
                                        fontWeight: FontWeight.w600),
                                    decoration: _inputDeco('Email Address',
                                        Icons.alternate_email_rounded),
                                    validator: (v) =>
                                        v == null || !v.contains('@')
                                            ? 'Invalid email'
                                            : null,
                                  ),
                                  const SizedBox(height: 16),
                                  TextFormField(
                                    controller: _passCtrl,
                                    obscureText: true,
                                    style: const TextStyle(
                                        color: Colors.white,
                                        fontWeight: FontWeight.w600),
                                    decoration: _inputDeco(
                                        'Password', Icons.lock_open_rounded),
                                    validator: (v) =>
                                        v == null || v.isEmpty
                                            ? 'Required'
                                            : null,
                                  ),
                                ],
                                const SizedBox(height: 32),
                                ElevatedButton(
                                  onPressed: (auth.isLoading || _sending) ? null : _submit,
                                  style: ElevatedButton.styleFrom(
                                    backgroundColor: Colors.white,
                                    foregroundColor: AppTheme.primary,
                                    minimumSize:
                                        const Size(double.infinity, 56),
                                    shape: RoundedRectangleBorder(
                                        borderRadius:
                                            BorderRadius.circular(16)),
                                    elevation: 0,
                                  ),
                                  child: auth.isLoading
                                      ? const CircularProgressIndicator()
                                      : Text(
                                          _isAdminMode
                                              ? 'LOGIN TO DASHBOARD'
                                              : s.sendOtp,
                                          style: const TextStyle(
                                              fontWeight: FontWeight.w800,
                                              fontSize: 16,
                                              letterSpacing: 1),
                                        ),
                                ),
                              ],
                            ),
                          ),
                        ),
                      ),
                    ),

                    const SizedBox(height: 24),

                    if (!_isAdminMode)
                      Center(
                        child: Text(
                          s.welcomeSub,
                          textAlign: TextAlign.center,
                          style: TextStyle(
                              fontSize: 13,
                              color: Colors.white.withOpacity(0.5),
                              height: 1.5),
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

class _AdminToggleButton extends StatelessWidget {
  final bool isAdmin;
  final VoidCallback onToggle;
  const _AdminToggleButton(
      {required this.isAdmin, required this.onToggle});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onToggle,
      child: Container(
        padding:
            const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        decoration: BoxDecoration(
          color: isAdmin
              ? AppTheme.primary
              : Colors.white.withOpacity(0.1),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
              color: isAdmin
                  ? Colors.white
                  : Colors.white.withOpacity(0.2)),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              isAdmin
                  ? Icons.admin_panel_settings_rounded
                  : Icons.person_outline_rounded,
              color: Colors.white,
              size: 16,
            ),
            const SizedBox(width: 8),
            Text(
              isAdmin ? 'ADMIN MODE' : 'SWITCH TO ADMIN',
              style: const TextStyle(
                color: Colors.white,
                fontWeight: FontWeight.w700,
                fontSize: 11,
                letterSpacing: 0.5,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
