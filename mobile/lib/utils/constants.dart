class AppConstants {
  // API
  // Use --dart-define=BASE_URL=https://your-api.com/api/v1 to override during build
  static const String baseUrl = String.fromEnvironment(
    'BASE_URL',
    defaultValue: 'https://gigshield-guidewire-devtrails.onrender.com/api/v1',
  );

  // Storage Keys
  static const String accessTokenKey = 'access_token';
  static const String refreshTokenKey = 'refresh_token';
  static const String workerIdKey = 'worker_id';
  static const String onboardingDoneKey = 'onboarding_done';
  static const String termsAcceptedKey = 'terms_accepted';

  // Policy Tier Labels
  static const Map<String, String> tierLabels = {
    'basic': 'Basic Shield',
    'smart': 'Smart Shield',
    'pro': 'Pro Shield',
  };

  // Tier Prices
  static const Map<String, double> tierBasePrices = {
    'basic': 29.0,
    'smart': 49.0,
    'pro': 79.0,
  };

  // Disruption Type Labels
  static const Map<String, String> disruptionLabels = {
    'heavy_rain': '🌧️ Heavy Rain',
    'extreme_heat': '🌡️ Extreme Heat',
    'aqi_spike': '🏭 AQI Spike',
    'traffic_disruption': '🚧 Traffic Disruption',
    'civic_emergency': '🚨 Civic Emergency',
  };

  // Severity Colors
  static const Map<String, int> severityColors = {
    'moderate': 0xFFF59E0B,
    'severe': 0xFFEF4444,
    'extreme': 0xFF991B1B,
  };

  // Cities
  static const List<String> supportedCities = [
    'Bangalore',
    'Mumbai',
    'Delhi',
    'Chennai',
    'Hyderabad',
    'Pune',
    'Kolkata',
  ];

  // Platforms — quick-commerce & food delivery (persona: Blinkit/Zepto/Swiggy Instamart)
  static const List<Map<String, String>> platforms = [
    {'value': 'blinkit',          'label': 'Blinkit',           'color': 'F8C002'},
    {'value': 'zepto',            'label': 'Zepto',             'color': '6C2BF5'},
    {'value': 'swiggy_instamart', 'label': 'Swiggy Instamart',  'color': 'FC8019'},
    {'value': 'zomato',           'label': 'Zomato',            'color': 'E23744'},
    {'value': 'amazon',           'label': 'Amazon',            'color': 'FF9900'},
    {'value': 'bigbasket',        'label': 'BigBasket',         'color': '84C225'},
  ];
}
