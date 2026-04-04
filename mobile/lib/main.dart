import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:susanoo/router/app_router.dart';
import 'package:susanoo/theme/app_theme.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await SystemChrome.setPreferredOrientations([DeviceOrientation.portraitUp]);
  SystemChrome.setSystemUIOverlayStyle(
    const SystemUiOverlayStyle(
      statusBarColor: Colors.transparent,
      statusBarIconBrightness: Brightness.dark,
    ),
  );
  runApp(const ProviderScope(child: SusanooApp()));
}

class SusanooApp extends ConsumerWidget {
  const SusanooApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final router = ref.watch(appRouterProvider);
    return MaterialApp.router(
      title: 'Susanoo',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.lightTheme,
      routerConfig: router,
      builder: (context, child) => _LocationPermissionWrapper(child: child!),
    );
  }
}

class _LocationPermissionWrapper extends StatefulWidget {
  final Widget child;
  const _LocationPermissionWrapper({required this.child});

  @override
  State<_LocationPermissionWrapper> createState() => _LocationPermissionWrapperState();
}

class _LocationPermissionWrapperState extends State<_LocationPermissionWrapper> {
  bool _checked = false;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _checkPermission());
  }

  Future<void> _checkPermission() async {
    final status = await Permission.locationWhenInUse.status;
    // Show our custom dialog if not granted OR if denied (but not permanently)
    if (!status.isGranted && mounted) {
      await Future.delayed(const Duration(milliseconds: 800));
      if (mounted) {
        if (status.isPermanentlyDenied) {
          // Guide user to settings
          _showSettingsDialog();
        } else {
          _showPermissionDialog();
        }
      }
    }
    setState(() => _checked = true);
  }

  void _showSettingsDialog() {
    showDialog(
      context: context,
      builder: (_) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        contentPadding: const EdgeInsets.all(24),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.location_off_rounded, color: AppTheme.warning, size: 48),
            const SizedBox(height: 16),
            const Text('Location Access Needed', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w800), textAlign: TextAlign.center),
            const SizedBox(height: 12),
            const Text('Please enable location in Settings to allow Susanoo to detect disruptions in your delivery zone.', style: TextStyle(fontSize: 14, color: AppTheme.textSecondary, height: 1.5), textAlign: TextAlign.center),
            const SizedBox(height: 24),
            SizedBox(width: double.infinity, child: ElevatedButton(onPressed: () { Navigator.pop(context); openAppSettings(); }, child: const Text('Open Settings'))),
            const SizedBox(height: 8),
            SizedBox(width: double.infinity, child: TextButton(onPressed: () => Navigator.pop(context), child: const Text('Not Now', style: TextStyle(color: AppTheme.textSecondary)))),
          ],
        ),
      ),
    );
  }

  void _showPermissionDialog() {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (_) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        contentPadding: const EdgeInsets.all(24),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: AppTheme.primaryLight,
                shape: BoxShape.circle,
              ),
              child: const Icon(Icons.location_on_rounded, color: AppTheme.primary, size: 36),
            ),
            const SizedBox(height: 20),
            const Text(
              'Allow Location Access',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.w800),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 12),
            const Text(
              'Susanoo uses your location to detect disruptions in your delivery zone and auto-trigger claims when weather or civic events affect your area.',
              style: TextStyle(fontSize: 14, color: AppTheme.textSecondary, height: 1.5),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 8),
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: const Color(0xFFFFF8E1),
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: const Color(0xFFFFE082)),
              ),
              child: const Row(
                children: [
                  Icon(Icons.info_outline_rounded, size: 14, color: Color(0xFFF59E0B)),
                  SizedBox(width: 6),
                  Expanded(
                    child: Text(
                      'You can change this anytime in Settings.',
                      style: TextStyle(fontSize: 11, color: Color(0xFF78350F)),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 24),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: () async {
                  Navigator.pop(context);
                  final result = await Permission.locationWhenInUse.request();
                  if (!result.isGranted && mounted) {
                    // If still denied after system dialog, show settings option
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(
                        content: const Text('Location helps detect disruptions in your zone.'),
                        action: SnackBarAction(label: 'Settings', onPressed: openAppSettings),
                      ),
                    );
                  }
                },
                child: const Text('Allow Location'),
              ),
            ),
            const SizedBox(height: 8),
            SizedBox(
              width: double.infinity,
              child: TextButton(
                onPressed: () => Navigator.pop(context),
                child: const Text(
                  'Not Now',
                  style: TextStyle(color: AppTheme.textSecondary),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) => widget.child;
}
