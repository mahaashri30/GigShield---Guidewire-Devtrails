import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:susanoo/l10n/app_strings.dart';

const _kLangKey = 'app_language';

class LocaleNotifier extends StateNotifier<String> {
  LocaleNotifier() : super('en') {
    _load();
  }

  Future<void> _load() async {
    final prefs = await SharedPreferences.getInstance();
    state = prefs.getString(_kLangKey) ?? 'en';
  }

  Future<void> setLanguage(String code) async {
    state = code;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_kLangKey, code);
  }
}

final localeProvider = StateNotifierProvider<LocaleNotifier, String>(
  (_) => LocaleNotifier(),
);

final stringsProvider = Provider<AppStrings>((ref) {
  return AppStrings.of(ref.watch(localeProvider));
});

final localeMaterialProvider = Provider<Locale>((ref) {
  return Locale(ref.watch(localeProvider));
});
