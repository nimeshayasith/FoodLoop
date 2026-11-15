import { createContext, useContext, useEffect, useState } from "react";

// NOTE: Sinhala and Tamil strings should be reviewed by native speakers before a public launch.
const dict = {
  en: {
    "nav.browse": "Browse food", "nav.reservations": "My reservations", "nav.dashboard": "Dashboard", "nav.admin": "Admin",
    "nav.signin": "Sign in", "nav.signout": "Sign out", "nav.profile": "Profile",
    tagline: "Buy smart. Share surplus. Waste less.",
    "hero.sub": "Supermarkets, bakeries and restaurants list surplus food at a discount. Whatever is left is automatically offered free to charities.",
    "cta.browse": "Find food near you", "cta.list": "List surplus food",
    "stats.rescued": "Items rescued", "stats.donated": "Items donated to charities", "stats.saved": "Saved by shoppers",
    "how.title": "How FoodLoop works",
    "how.1": "Stores list surplus food at a reduced price", "how.2": "You reserve it and collect from the store with a pickup code",
    "how.3": "Unsold food is automatically offered free to verified charities",
    "type.DISCOUNTED": "Smart deal", "type.DONATION": "Free donation",
    "filter.all": "All", "filter.district": "District", "filter.category": "Category", "filter.search": "Search food or store",
    "filter.alldistricts": "All districts", "filter.allcategories": "All categories",
    "listing.left": "left", "listing.free": "FREE", "listing.reserveBy": "Reserve within", "listing.collectBy": "Collect by",
    "listing.reserve": "Reserve", "listing.quantity": "Quantity", "listing.noResults": "No food listed right now. Check back soon!",
    "listing.charityOnly": "Donations are only for verified charities and community groups.",
    "listing.converted": "Unsold deal converted to a free donation", "listing.closed": "Closed",
    "listing.limit": "Max per customer", "listing.pickup": "Pickup", "listing.bestBefore": "Best before",
    "listing.signinToReserve": "Sign in to reserve", "listing.completeProfile": "Complete your profile to reserve",
    whatsapp: "Chat on WhatsApp",
    "res.title": "My reservations", "res.code": "Pickup code", "res.show": "Show this code at the counter", "res.cancel": "Cancel",
    "res.empty": "You have no reservations yet.",
    "status.RESERVED": "Reserved", "status.COLLECTED": "Collected", "status.CANCELLED": "Cancelled", "status.NO_SHOW": "Not collected",
  },
  si: {
    "nav.browse": "ආහාර බලන්න", "nav.reservations": "මගේ වෙන්කිරීම්", "nav.dashboard": "උපකරණ පුවරුව", "nav.admin": "පරිපාලක",
    "nav.signin": "පිවිසෙන්න", "nav.signout": "ඉවත් වන්න", "nav.profile": "පැතිකඩ",
    tagline: "දක්ෂව මිල දී ගන්න. අතිරික්තය බෙදාගන්න. නාස්තිය අඩු කරන්න.",
    "hero.sub": "සුපිරි වෙළඳසැල්, බේකරි සහ අවන්හල් අතිරික්ත ආහාර වට්ටමකට ලබා දෙයි. ඉතිරි වන ඒවා ස්වයංක්‍රීයව පුණ්‍යායතනවලට නොමිලේ ලබා දෙයි.",
    "cta.browse": "ඔබ අසල ආහාර සොයන්න", "cta.list": "අතිරික්ත ආහාර ඇතුළත් කරන්න",
    "stats.rescued": "ගලවාගත් භාණ්ඩ", "stats.donated": "පුණ්‍යායතනවලට පරිත්‍යාග කළ භාණ්ඩ", "stats.saved": "ගැනුම්කරුවන් ඉතිරි කළ මුදල",
    "how.title": "FoodLoop ක්‍රියා කරන ආකාරය",
    "how.1": "වෙළඳසැල් අතිරික්ත ආහාර අඩු මිලට ඇතුළත් කරයි", "how.2": "ඔබ වෙන් කර, ලබාගැනීමේ කේතය සමඟ වෙළඳසැලෙන් රැගෙන යයි",
    "how.3": "අලෙවි නොවූ ආහාර සත්‍යාපිත පුණ්‍යායතනවලට ස්වයංක්‍රීයව නොමිලේ ලබා දෙයි",
    "type.DISCOUNTED": "වට්ටම් දීමනාව", "type.DONATION": "නොමිලේ පරිත්‍යාගය",
    "filter.all": "සියල්ල", "filter.district": "දිස්ත්‍රික්කය", "filter.category": "කාණ්ඩය", "filter.search": "ආහාර හෝ වෙළඳසැල සොයන්න",
    "filter.alldistricts": "සියලු දිස්ත්‍රික්ක", "filter.allcategories": "සියලු කාණ්ඩ",
    "listing.left": "ඉතිරියි", "listing.free": "නොමිලේ", "listing.reserveBy": "වෙන් කළ යුතු කාලය", "listing.collectBy": "රැගෙන යා යුතු අවසන් වේලාව",
    "listing.reserve": "වෙන් කරන්න", "listing.quantity": "ප්‍රමාණය", "listing.noResults": "දැනට ආහාර නොමැත. ඉක්මනින් නැවත බලන්න!",
    "listing.charityOnly": "පරිත්‍යාග සත්‍යාපිත පුණ්‍යායතන සහ ප්‍රජා කණ්ඩායම් සඳහා පමණි.",
    "listing.converted": "අලෙවි නොවූ දීමනාව නොමිලේ පරිත්‍යාගයක් බවට පත් විය", "listing.closed": "අවසන්",
    "listing.limit": "එක් පාරිභෝගිකයෙකුට උපරිමය", "listing.pickup": "රැගෙන යාම", "listing.bestBefore": "මෙයට පෙර භාවිත කරන්න",
    "listing.signinToReserve": "වෙන් කිරීමට පිවිසෙන්න", "listing.completeProfile": "වෙන් කිරීමට ඔබේ පැතිකඩ සම්පූර්ණ කරන්න",
    whatsapp: "WhatsApp හරහා කතා කරන්න",
    "res.title": "මගේ වෙන්කිරීම්", "res.code": "ලබාගැනීමේ කේතය", "res.show": "මෙම කේතය කවුන්ටරයේදී පෙන්වන්න", "res.cancel": "අවලංගු කරන්න",
    "res.empty": "ඔබට තවම වෙන්කිරීම් නැත.",
    "status.RESERVED": "වෙන්කර ඇත", "status.COLLECTED": "රැගෙන ගොස් ඇත", "status.CANCELLED": "අවලංගු කර ඇත", "status.NO_SHOW": "රැගෙන ගොස් නැත",
  },
  ta: {
    "nav.browse": "உணவைப் பார்க்க", "nav.reservations": "என் முன்பதிவுகள்", "nav.dashboard": "டாஷ்போர்டு", "nav.admin": "நிர்வாகம்",
    "nav.signin": "உள்நுழை", "nav.signout": "வெளியேறு", "nav.profile": "சுயவிவரம்",
    tagline: "புத்திசாலித்தனமாக வாங்குங்கள். மிகுதியைப் பகிருங்கள். வீணாக்குவதைக் குறையுங்கள்.",
    "hero.sub": "பல்பொருள் அங்காடிகள், பேக்கரிகள், உணவகங்கள் மிகுதி உணவைத் தள்ளுபடி விலையில் வழங்குகின்றன. மீதமுள்ளவை தானாகவே அறக்கட்டளைகளுக்கு இலவசமாக வழங்கப்படும்.",
    "cta.browse": "உங்கள் அருகில் உணவைத் தேடுங்கள்", "cta.list": "மிகுதி உணவைப் பதிவிடுங்கள்",
    "stats.rescued": "மீட்கப்பட்ட பொருட்கள்", "stats.donated": "அறக்கட்டளைகளுக்கு வழங்கிய பொருட்கள்", "stats.saved": "வாங்குவோர் சேமித்த தொகை",
    "how.title": "FoodLoop எப்படி செயல்படுகிறது",
    "how.1": "கடைகள் மிகுதி உணவைக் குறைந்த விலையில் பதிவிடுகின்றன", "how.2": "நீங்கள் முன்பதிவு செய்து, குறியீட்டுடன் கடையில் பெற்றுக்கொள்ளுங்கள்",
    "how.3": "விற்கப்படாத உணவு சரிபார்க்கப்பட்ட அறக்கட்டளைகளுக்கு தானாகவே இலவசமாக வழங்கப்படும்",
    "type.DISCOUNTED": "தள்ளுபடி சலுகை", "type.DONATION": "இலவச நன்கொடை",
    "filter.all": "அனைத்தும்", "filter.district": "மாவட்டம்", "filter.category": "வகை", "filter.search": "உணவு அல்லது கடையைத் தேடுங்கள்",
    "filter.alldistricts": "அனைத்து மாவட்டங்களும்", "filter.allcategories": "அனைத்து வகைகளும்",
    "listing.left": "மீதம்", "listing.free": "இலவசம்", "listing.reserveBy": "முன்பதிவு செய்ய உள்ள நேரம்", "listing.collectBy": "பெற்றுக்கொள்ள கடைசி நேரம்",
    "listing.reserve": "முன்பதிவு செய்", "listing.quantity": "அளவு", "listing.noResults": "தற்போது உணவு இல்லை. விரைவில் மீண்டும் பாருங்கள்!",
    "listing.charityOnly": "நன்கொடைகள் சரிபார்க்கப்பட்ட அறக்கட்டளைகள் மற்றும் சமூகக் குழுக்களுக்கு மட்டுமே.",
    "listing.converted": "விற்கப்படாத சலுகை இலவச நன்கொடையாக மாற்றப்பட்டது", "listing.closed": "முடிந்தது",
    "listing.limit": "ஒருவருக்கு அதிகபட்சம்", "listing.pickup": "பெறுதல்", "listing.bestBefore": "இதற்குள் பயன்படுத்தவும்",
    "listing.signinToReserve": "முன்பதிவு செய்ய உள்நுழையுங்கள்", "listing.completeProfile": "முன்பதிவு செய்ய உங்கள் சுயவிவரத்தை நிரப்புங்கள்",
    whatsapp: "WhatsApp இல் பேசுங்கள்",
    "res.title": "என் முன்பதிவுகள்", "res.code": "பெறுவதற்கான குறியீடு", "res.show": "இந்தக் குறியீட்டை கவுண்டரில் காட்டுங்கள்", "res.cancel": "ரத்து செய்",
    "res.empty": "உங்களுக்கு இதுவரை முன்பதிவுகள் இல்லை.",
    "status.RESERVED": "முன்பதிவு", "status.COLLECTED": "பெறப்பட்டது", "status.CANCELLED": "ரத்து", "status.NO_SHOW": "பெறவில்லை",
  },
};

export const LANGS = [["en", "English"], ["si", "සිංහල"], ["ta", "தமிழ்"]];
const I18nContext = createContext(null);
export const useI18n = () => useContext(I18nContext);

export function I18nProvider({ children }) {
  const [lang, setLang] = useState(() => localStorage.getItem("foodloop.lang") || "en");
  useEffect(() => { localStorage.setItem("foodloop.lang", lang); document.documentElement.lang = lang; }, [lang]);
  const t = (key) => dict[lang]?.[key] ?? dict.en[key] ?? key;
  return <I18nContext.Provider value={{ lang, setLang, t }}>{children}</I18nContext.Provider>;
}
