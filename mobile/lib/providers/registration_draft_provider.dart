import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Persists registration form draft across app restarts.
/// Keys are stored in SharedPreferences so closing the app mid-form
/// does not lose the user's input.
class RegistrationDraft {
  final String name;
  final String city;
  final String pincode;
  final String upiId;
  final String platform;

  const RegistrationDraft({
    this.name = '',
    this.city = '',
    this.pincode = '',
    this.upiId = '',
    this.platform = '',
  });

  RegistrationDraft copyWith({
    String? name,
    String? city,
    String? pincode,
    String? upiId,
    String? platform,
  }) =>
      RegistrationDraft(
        name: name ?? this.name,
        city: city ?? this.city,
        pincode: pincode ?? this.pincode,
        upiId: upiId ?? this.upiId,
        platform: platform ?? this.platform,
      );

  bool get isEmpty =>
      name.isEmpty && city.isEmpty && pincode.isEmpty && upiId.isEmpty;
}

class RegistrationDraftNotifier extends StateNotifier<RegistrationDraft> {
  static const _kName = 'reg_draft_name';
  static const _kCity = 'reg_draft_city';
  static const _kPincode = 'reg_draft_pincode';
  static const _kUpi = 'reg_draft_upi';
  static const _kPlatform = 'reg_draft_platform';

  RegistrationDraftNotifier() : super(const RegistrationDraft()) {
    _load();
  }

  Future<void> _load() async {
    final prefs = await SharedPreferences.getInstance();
    state = RegistrationDraft(
      name: prefs.getString(_kName) ?? '',
      city: prefs.getString(_kCity) ?? '',
      pincode: prefs.getString(_kPincode) ?? '',
      upiId: prefs.getString(_kUpi) ?? '',
      platform: prefs.getString(_kPlatform) ?? '',
    );
  }

  Future<void> update({
    String? name,
    String? city,
    String? pincode,
    String? upiId,
    String? platform,
  }) async {
    state = state.copyWith(
      name: name,
      city: city,
      pincode: pincode,
      upiId: upiId,
      platform: platform,
    );
    final prefs = await SharedPreferences.getInstance();
    if (name != null) await prefs.setString(_kName, name);
    if (city != null) await prefs.setString(_kCity, city);
    if (pincode != null) await prefs.setString(_kPincode, pincode);
    if (upiId != null) await prefs.setString(_kUpi, upiId);
    if (platform != null) await prefs.setString(_kPlatform, platform);
  }

  Future<void> clear() async {
    state = const RegistrationDraft();
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_kName);
    await prefs.remove(_kCity);
    await prefs.remove(_kPincode);
    await prefs.remove(_kUpi);
    await prefs.remove(_kPlatform);
  }
}

final registrationDraftProvider =
    StateNotifierProvider<RegistrationDraftNotifier, RegistrationDraft>(
  (_) => RegistrationDraftNotifier(),
);
