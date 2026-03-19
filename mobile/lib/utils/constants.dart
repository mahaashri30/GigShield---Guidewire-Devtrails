class AppConstants {
  // API
  // Android emulator on Windows — 10.0.2.2 maps to your PC's localhost
  static const String baseUrl = 'http://10.0.2.2:8000/api/v1';
  // Real device on same WiFi — replace with your PC's local IP:
  // static const String baseUrl = 'http://192.168.x.x:8000/api/v1';
  // Deployed backend:
  // static const String baseUrl = 'https://gigshield-api.onrender.com/api/v1';

  // Storage Keys
  static const String accessTokenKey = 'access_token';
  static const String refreshTokenKey = 'refresh_token';
  static const String workerIdKey = 'worker_id';
  static const String onboardingDoneKey = 'onboarding_done';

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

  // Platforms
  static const List<Map<String, String>> platforms = [
    {'value': 'zomato', 'label': 'Zomato', 'color': 'E23744'},
    {'value': 'swiggy', 'label': 'Swiggy', 'color': 'FC8019'},
    {'value': 'dunzo', 'label': 'Dunzo', 'color': '00C28E'},
    {'value': 'blinkit', 'label': 'Blinkit', 'color': 'F8C002'},
    {'value': 'zepto', 'label': 'Zepto', 'color': '6C2BF5'},
    {'value': 'amazon', 'label': 'Amazon', 'color': 'FF9900'},
  ];
}
