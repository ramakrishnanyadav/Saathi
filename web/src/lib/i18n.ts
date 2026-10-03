import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

const resources = {
  en: {
    translation: {
      appName: 'SAATH',
      brandSub: 'Your Household Memory & Follow-Through',
      heroTitle: "One person shouldn't run the whole house.",
      heroSub: 'SAATH remembers promises, keeps track of open problems, and handles gentle follow-ups so your mind stays clear.',
      devanagariTag: 'साथ',
      nav: {
        today: 'Needs Attention',
        history: 'Household History',
        people: 'People',
        money: 'Expenses',
        week: 'Weekly Summary',
        supplies: 'Supplies',
        privacy: 'Local Proof',
        lab: 'Time Machine',
        settings: 'Settings',
        add: 'Tell SAATH',
      },
      attention: {
        title: 'Needs Attention',
        sub: 'Open promises and gentle follow-ups',
        allClearTitle: 'All Clear!',
        allClearSub: 'Nothing needs your attention right now. SAATH is keeping watch.',
        needsAction: 'Needs action',
        waiting: 'Waiting on others',
        done: 'Done',
        sendFollowup: 'Send check-in',
        overdueBy: 'Overdue by',
        snooze: 'Remind later',
        markDone: 'Mark completed',
      },
      composer: {
        placeholder: 'What happened?',
        hint: 'Press Enter to submit · Shift+Enter for new line',
        understanding: 'Understanding...',
        micIdle: 'Hold to talk',
        micRecording: 'Listening...',
      },
      week: {
        title: "This Week's Household Summary",
        sub: 'Invisible coordination & care work across the home',
        noScoreboard: 'SAATH never ranks or scores people. All contributions matter equally.',
      },
    },
  },
  hinglish: {
    translation: {
      appName: 'SAATH',
      brandSub: 'Ghar ki memory aur follow-through',
      heroTitle: 'Ek insaan pure ghar ko akele nahi chala sakta.',
      heroSub: 'SAATH vaade yaad rakhta hai, dikkatoon ka hisaab rakhta hai, aur pyaar se check-in karta hai.',
      devanagariTag: 'साथ',
      nav: {
        today: 'Dhyaan Chahiye',
        history: 'Ghar ka Itihaas',
        people: 'Log',
        money: 'Kharcha',
        week: 'Hafte ki Summary',
        supplies: 'Rashan & Stuff',
        privacy: 'Local Proof',
        lab: 'Ghadi (Time Machine)',
        settings: 'Settings',
        add: 'SAATH ko Bato',
      },
      attention: {
        title: 'Dhyaan Chahiye',
        sub: 'Khule vaade aur zaroori follow-ups',
        allClearTitle: 'Sab Shaant Hai!',
        allClearSub: 'Abhi koi tension nahi. SAATH sab yaad rakh raha hai.',
        needsAction: 'Action chahiye',
        waiting: 'Intezaar hai',
        done: 'Ho gaya',
        sendFollowup: 'Check-in bhejo',
        overdueBy: 'Der ho gayi',
        snooze: 'Baad mein',
        markDone: 'Khatam hua',
      },
      composer: {
        placeholder: 'Kya hua?',
        hint: 'Enter dabayein bhejne ke liye',
        understanding: 'Samajh raha hoon...',
        micIdle: 'Bolne ke liye dabayein',
        micRecording: 'Sun raha hoon...',
      },
      week: {
        title: 'Is Hafte Ki Summary',
        sub: 'Ghar ka invisible kaam aur dekhbhal',
        noScoreboard: 'SAATH kisi ko rank ya compare nahi karta. Har kaam barabar hai.',
      },
    },
  },
  hi: {
    translation: {
      appName: 'साथ',
      brandSub: 'घर की याददाश्त और फॉलो-थ्रू',
      heroTitle: 'एक इंसान पूरे घर को अकेले नहीं चला सकता।',
      heroSub: 'साथ वादे याद रखता है, समस्याओं का ध्यान रखता है, और प्यार से फॉलो-अप करता है।',
      devanagariTag: 'साथ',
      nav: {
        today: 'ध्यान चाहिए',
        history: 'घर का इतिहास',
        people: 'सदस्य',
        money: 'खर्च',
        week: 'साप्ताहिक सारांश',
        supplies: 'सामग्री',
        privacy: 'लोकल प्रूफ',
        lab: 'समय मशीन',
        settings: 'सेटिंग्स',
        add: 'साथ को बताएं',
      },
      attention: {
        title: 'ध्यान चाहिए',
        sub: 'खुले वादे और जरूरी चेक-इन',
        allClearTitle: 'सब शांत है!',
        allClearSub: 'अभी किसी कार्रवाई की आवश्यकता नहीं है।',
        needsAction: 'कार्रवाई चाहिए',
        waiting: 'प्रतीक्षा में',
        done: 'पूर्ण',
        sendFollowup: 'चेक-इन भेजें',
        overdueBy: 'देरी',
        snooze: 'बाद में',
        markDone: 'पूर्ण चिन्हित करें',
      },
      composer: {
        placeholder: 'क्या हुआ?',
        hint: 'भेजने के लिए एंटर दबाएं',
        understanding: 'समझ रहा हूँ...',
        micIdle: 'बोलने के लिए दबाएं',
        micRecording: 'सुन रहा हूँ...',
      },
      week: {
        title: 'इस सप्ताह का सारांश',
        sub: 'घर का अदृश्य कार्य और देखभाल',
        noScoreboard: 'साथ कभी किसी की तुलना नहीं करता। हर योगदान महत्वपूर्ण है।',
      },
    },
  },
};

i18n.use(initReactI18next).init({
  resources,
  lng: 'hinglish', // default Hinglish for warm cultural feel
  fallbackLng: 'en',
  interpolation: {
    escapeValue: false,
  },
});

export default i18n;
