class AppStrings {
  final String languageName;
  final String welcome;
  final String welcomeSub;
  final String mobileNumber;
  final String sendOtp;
  final String sendingOtp;
  final String enterOtp;
  final String verify;
  final String verifying;
  final String profile;
  final String accountDetails;
  final String riskProfile;
  final String logout;
  final String mobile;
  final String upiId;
  final String city;
  final String avgDailyEarnings;
  final String riskScore;
  final String language;
  final String allowLocation;
  final String allowLocationDesc;
  final String locationNeeded;
  final String locationNeededDesc;
  final String openSettings;
  final String notNow;
  final String allowLocationBtn;
  final String changeAnytime;
  final String home;
  final String claims;
  final String policy;
  final String noPolicyActive;
  final String buyPolicy;
  final String activeDisruptions;
  final String noDisruptions;
  final String pending;
  final String approved;
  final String paid;
  final String termsPrivacy;
  final String howItWorks;
  final String howItWorksReal;
  final String howItWorksDemo;
  final String serverWakeup;
  final String invalidPhone;
  final String selectPlatform;
  final String selectCity;
  final String yourName;
  final String upiIdHint;
  final String avgEarningsHint;
  final String register;
  final String registering;
  final String selectLanguage;

  const AppStrings({
    required this.languageName,
    required this.welcome,
    required this.welcomeSub,
    required this.mobileNumber,
    required this.sendOtp,
    required this.sendingOtp,
    required this.enterOtp,
    required this.verify,
    required this.verifying,
    required this.profile,
    required this.accountDetails,
    required this.riskProfile,
    required this.logout,
    required this.mobile,
    required this.upiId,
    required this.city,
    required this.avgDailyEarnings,
    required this.riskScore,
    required this.language,
    required this.allowLocation,
    required this.allowLocationDesc,
    required this.locationNeeded,
    required this.locationNeededDesc,
    required this.openSettings,
    required this.notNow,
    required this.allowLocationBtn,
    required this.changeAnytime,
    required this.home,
    required this.claims,
    required this.policy,
    required this.noPolicyActive,
    required this.buyPolicy,
    required this.activeDisruptions,
    required this.noDisruptions,
    required this.pending,
    required this.approved,
    required this.paid,
    required this.termsPrivacy,
    required this.howItWorks,
    required this.howItWorksReal,
    required this.howItWorksDemo,
    required this.serverWakeup,
    required this.invalidPhone,
    required this.selectPlatform,
    required this.selectCity,
    required this.yourName,
    required this.upiIdHint,
    required this.avgEarningsHint,
    required this.register,
    required this.registering,
    required this.selectLanguage,
  });

  static const Map<String, AppStrings> all = {'en': _en, 'ta': _ta, 'hi': _hi};

  static AppStrings of(String code) => all[code] ?? _en;
}

const _en = AppStrings(
  languageName: 'English',
  welcome: 'Welcome to\nSusanoo 🛡️',
  welcomeSub: '"The Ultimate Defense" for delivery heroes.\nEnter your mobile number to get started.',
  mobileNumber: 'Mobile Number',
  sendOtp: 'Send OTP',
  sendingOtp: 'Sending OTP...',
  enterOtp: 'Enter OTP',
  verify: 'Verify',
  verifying: 'Verifying...',
  profile: 'Profile',
  accountDetails: 'Account Details',
  riskProfile: 'Risk Profile',
  logout: 'Logout',
  mobile: 'Mobile',
  upiId: 'UPI ID',
  city: 'City',
  avgDailyEarnings: 'Avg Daily Earnings',
  riskScore: 'Risk Score',
  language: 'Language',
  allowLocation: 'Allow Location Access',
  allowLocationDesc: 'Susanoo uses your location to detect disruptions in your delivery zone and auto-trigger claims when weather or civic events affect your area.',
  locationNeeded: 'Location Access Needed',
  locationNeededDesc: 'Please enable location in Settings to allow Susanoo to detect disruptions in your delivery zone.',
  openSettings: 'Open Settings',
  notNow: 'Not Now',
  allowLocationBtn: 'Allow Location',
  changeAnytime: 'You can change this anytime in Settings.',
  home: 'Home',
  claims: 'Claims',
  policy: 'Policy',
  noPolicyActive: 'No active policy',
  buyPolicy: 'Buy Policy',
  activeDisruptions: 'Active Disruptions',
  noDisruptions: 'No active disruptions',
  pending: 'Pending',
  approved: 'Approved',
  paid: 'Paid',
  termsPrivacy: 'By continuing, you agree to our Terms & Privacy Policy',
  howItWorks: 'How it works',
  howItWorksReal: '• Real users: Enter your registered mobile number to receive a live OTP via SMS.',
  howItWorksDemo: '• Demo / Testing: Use any number and enter OTP 123456 to explore the app in demo mode.',
  serverWakeup: 'Please wait up to 30 seconds\nfor the server to wake up.',
  invalidPhone: 'Enter a valid 10-digit number',
  selectPlatform: 'Select Platform',
  selectCity: 'Select City',
  yourName: 'Your Name',
  upiIdHint: 'yourname@upi',
  avgEarningsHint: 'Average daily earnings (₹)',
  register: 'Complete Registration',
  registering: 'Registering...',
  selectLanguage: 'Select Language',
);

const _ta = AppStrings(
  languageName: 'தமிழ்',
  welcome: 'சுசானூவிற்கு\nவரவேற்கிறோம் 🛡️',
  welcomeSub: 'டெலிவரி ஹீரோக்களுக்கான "இறுதி பாதுகாப்பு".\nதொடங்க உங்கள் மொபைல் எண்ணை உள்ளிடவும்.',
  mobileNumber: 'மொபைல் எண்',
  sendOtp: 'OTP அனுப்பு',
  sendingOtp: 'OTP அனுப்புகிறது...',
  enterOtp: 'OTP உள்ளிடவும்',
  verify: 'சரிபார்',
  verifying: 'சரிபார்க்கிறது...',
  profile: 'சுயவிவரம்',
  accountDetails: 'கணக்கு விவரங்கள்',
  riskProfile: 'ரிஸ்க் சுயவிவரம்',
  logout: 'வெளியேறு',
  mobile: 'மொபைல்',
  upiId: 'UPI ஐடி',
  city: 'நகரம்',
  avgDailyEarnings: 'சராசரி தினசரி வருமானம்',
  riskScore: 'ரிஸ்க் மதிப்பெண்',
  language: 'மொழி',
  allowLocation: 'இருப்பிட அணுகலை அனுமதிக்கவும்',
  allowLocationDesc: 'உங்கள் டெலிவரி மண்டலத்தில் இடையூறுகளை கண்டறிய சுசானூ உங்கள் இருப்பிடத்தை பயன்படுத்துகிறது.',
  locationNeeded: 'இருப்பிட அணுகல் தேவை',
  locationNeededDesc: 'சுசானூ உங்கள் டெலிவரி மண்டலத்தில் இடையூறுகளை கண்டறிய அமைப்புகளில் இருப்பிடத்தை இயக்கவும்.',
  openSettings: 'அமைப்புகளை திற',
  notNow: 'இப்போது வேண்டாம்',
  allowLocationBtn: 'இருப்பிடத்தை அனுமதி',
  changeAnytime: 'இதை எப்போது வேண்டுமானாலும் அமைப்புகளில் மாற்றலாம்.',
  home: 'முகப்பு',
  claims: 'கோரிக்கைகள்',
  policy: 'பாலிசி',
  noPolicyActive: 'செயலில் உள்ள பாலிசி இல்லை',
  buyPolicy: 'பாலிசி வாங்கு',
  activeDisruptions: 'செயலில் உள்ள இடையூறுகள்',
  noDisruptions: 'செயலில் உள்ள இடையூறுகள் இல்லை',
  pending: 'நிலுவையில்',
  approved: 'அங்கீகரிக்கப்பட்டது',
  paid: 'செலுத்தப்பட்டது',
  termsPrivacy: 'தொடர்வதன் மூலம், எங்கள் விதிமுறைகள் & தனியுரிமைக் கொள்கையை ஒப்புக்கொள்கிறீர்கள்',
  howItWorks: 'எப்படி செயல்படுகிறது',
  howItWorksReal: '• உண்மையான பயனர்கள்: SMS மூலம் நேரடி OTP பெற உங்கள் பதிவு செய்யப்பட்ட மொபைல் எண்ணை உள்ளிடவும்.',
  howItWorksDemo: '• டெமோ / சோதனை: எந்த எண்ணையும் பயன்படுத்தி OTP 123456 உள்ளிட்டு டெமோ பயன்முறையை ஆராயவும்.',
  serverWakeup: 'சர்வர் விழிப்படைய\n30 வினாடிகள் வரை காத்திருக்கவும்.',
  invalidPhone: 'சரியான 10 இலக்க எண்ணை உள்ளிடவும்',
  selectPlatform: 'தளத்தை தேர்ந்தெடுக்கவும்',
  selectCity: 'நகரத்தை தேர்ந்தெடுக்கவும்',
  yourName: 'உங்கள் பெயர்',
  upiIdHint: 'yourname@upi',
  avgEarningsHint: 'சராசரி தினசரி வருமானம் (₹)',
  register: 'பதிவை முடிக்கவும்',
  registering: 'பதிவு செய்கிறது...',
  selectLanguage: 'மொழியை தேர்ந்தெடுக்கவும்',
);

const _hi = AppStrings(
  languageName: 'हिंदी',
  welcome: 'सुसानू में\nआपका स्वागत है 🛡️',
  welcomeSub: 'डिलीवरी हीरोज़ के लिए "अंतिम सुरक्षा".\nशुरू करने के लिए अपना मोबाइल नंबर दर्ज करें।',
  mobileNumber: 'मोबाइल नंबर',
  sendOtp: 'OTP भेजें',
  sendingOtp: 'OTP भेजा जा रहा है...',
  enterOtp: 'OTP दर्ज करें',
  verify: 'सत्यापित करें',
  verifying: 'सत्यापित हो रहा है...',
  profile: 'प्रोफ़ाइल',
  accountDetails: 'खाता विवरण',
  riskProfile: 'जोखिम प्रोफ़ाइल',
  logout: 'लॉग आउट',
  mobile: 'मोबाइल',
  upiId: 'UPI आईडी',
  city: 'शहर',
  avgDailyEarnings: 'औसत दैनिक आय',
  riskScore: 'जोखिम स्कोर',
  language: 'भाषा',
  allowLocation: 'स्थान पहुँच की अनुमति दें',
  allowLocationDesc: 'सुसानू आपके डिलीवरी क्षेत्र में व्यवधानों का पता लगाने के लिए आपके स्थान का उपयोग करता है।',
  locationNeeded: 'स्थान पहुँच आवश्यक है',
  locationNeededDesc: 'सुसानू को आपके डिलीवरी क्षेत्र में व्यवधानों का पता लगाने के लिए सेटिंग्स में स्थान सक्षम करें।',
  openSettings: 'सेटिंग्स खोलें',
  notNow: 'अभी नहीं',
  allowLocationBtn: 'स्थान की अनुमति दें',
  changeAnytime: 'आप इसे कभी भी सेटिंग्स में बदल सकते हैं।',
  home: 'होम',
  claims: 'दावे',
  policy: 'पॉलिसी',
  noPolicyActive: 'कोई सक्रिय पॉलिसी नहीं',
  buyPolicy: 'पॉलिसी खरीदें',
  activeDisruptions: 'सक्रिय व्यवधान',
  noDisruptions: 'कोई सक्रिय व्यवधान नहीं',
  pending: 'लंबित',
  approved: 'स्वीकृत',
  paid: 'भुगतान किया',
  termsPrivacy: 'जारी रखकर, आप हमारी शर्तें और गोपनीयता नीति से सहमत हैं',
  howItWorks: 'यह कैसे काम करता है',
  howItWorksReal: '• वास्तविक उपयोगकर्ता: SMS के माध्यम से लाइव OTP प्राप्त करने के लिए अपना पंजीकृत मोबाइल नंबर दर्ज करें।',
  howItWorksDemo: '• डेमो / परीक्षण: कोई भी नंबर उपयोग करें और डेमो मोड में ऐप देखने के लिए OTP 123456 दर्ज करें।',
  serverWakeup: 'सर्वर के जागने के लिए\n30 सेकंड तक प्रतीक्षा करें।',
  invalidPhone: 'वैध 10 अंकों का नंबर दर्ज करें',
  selectPlatform: 'प्लेटफ़ॉर्म चुनें',
  selectCity: 'शहर चुनें',
  yourName: 'आपका नाम',
  upiIdHint: 'yourname@upi',
  avgEarningsHint: 'औसत दैनिक आय (₹)',
  register: 'पंजीकरण पूरा करें',
  registering: 'पंजीकरण हो रहा है...',
  selectLanguage: 'भाषा चुनें',
);
