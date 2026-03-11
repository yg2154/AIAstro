import asyncio
import logging
from abc import ABC, abstractmethod
from functools import lru_cache
from typing import List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Stub templates: all 12 signs × 5 intents, English + Hindi
# ---------------------------------------------------------------------------
_STUB_EN = {
    "Aries": {
        "career": (
            "As an Aries, your Mars-ruled fire energy makes you a natural pioneer. "
            "You excel in roles that demand courage and initiative—entrepreneurship, athletics, or leadership positions. "
            "This is a strong time to assert yourself professionally. Trust your instincts and take decisive action."
        ),
        "love": (
            "Aries in love is passionate and direct. You need a partner who matches your enthusiasm. "
            "Focus on channeling your fire into patience—love deepens when you slow down enough to truly listen."
        ),
        "spiritual": (
            "Your spiritual path, Aries, runs through action. Karma yoga—acting without attachment to results—is your sadhana. "
            "Physical practices like Surya Namaskar and martial arts transmute your Mars fire into spiritual energy."
        ),
        "planetary": (
            "Mars, your ruling planet, governs energy, courage, and ambition. When Mars is strong in transit, "
            "you feel an irresistible drive to initiate. Honor this energy by channeling it into disciplined action."
        ),
        "nakshatra": (
            "The nakshatras most aligned with Aries energy—Ashwini, Bharani, and Krittika—bring swiftness, "
            "transformation, and the purifying fire of courage. Your birth star reveals the soul's deeper calling."
        ),
    },
    "Taurus": {
        "career": (
            "Taurus, governed by Venus, thrives in careers that involve beauty, stability, and material mastery. "
            "Finance, real estate, culinary arts, and music suit you beautifully. Your patience is your greatest professional asset—"
            "you build what lasts."
        ),
        "love": (
            "In love, Taurus is the most devoted and sensual of all signs. You give everything once committed. "
            "Venus asks you to open your heart without possessiveness—true love flows freely."
        ),
        "spiritual": (
            "For Taurus, nature is the great temple. Gardening, walking barefoot, and sacred music open spiritual doors. "
            "Venus's higher octave is unconditional love—let beauty lead you to the divine."
        ),
        "planetary": (
            "Venus blesses Taurus with appreciation for beauty and comfort. When Venus transits favorably, "
            "creativity, love, and financial abundance flow. Honor Venus through art, gratitude, and service."
        ),
        "nakshatra": (
            "Rohini—the most beloved nakshatra of the Moon—falls in Taurus and bestows great creative and sensual gifts. "
            "If born under Rohini, you carry a deep capacity for beauty and nourishment."
        ),
    },
    "Gemini": {
        "career": (
            "Gemini's Mercury-ruled mind excels at communication, analysis, and connection. "
            "Journalism, technology, teaching, consulting, and digital media are natural fits. "
            "Your versatility is an asset—learn to focus it for maximum professional impact."
        ),
        "love": (
            "Gemini needs a partner who stimulates the mind. Intellectual chemistry is non-negotiable for you. "
            "Work on consistency—love deepens when you stay present rather than chasing the next exciting idea."
        ),
        "spiritual": (
            "Mercury's gift to Gemini is the discriminating mind (viveka). Study of sacred texts, mantra practice, "
            "and silent meditation quiet the chattering mind and reveal the stillness beneath all thoughts."
        ),
        "planetary": (
            "Mercury governs your quick mind, communication, and analytical power. "
            "During Mercury's strong transits, business deals, learning, and communication flourish. "
            "Mercury retrograde periods call for review and reflection rather than new initiatives."
        ),
        "nakshatra": (
            "Mrigashira, Ardra, and Punarvasu fall in Gemini—representing seeking, transformation, and return to light. "
            "Your nakshatra shows which of these soul-themes is most central to your path."
        ),
    },
    "Cancer": {
        "career": (
            "Cancer's Moon-ruled intuition and nurturing instinct shine in healthcare, education, hospitality, "
            "and real estate. You thrive where you can protect and care for others. "
            "Your emotional intelligence is your greatest professional asset."
        ),
        "love": (
            "Cancer loves with the whole heart and seeks emotional security above all. "
            "You are the most nurturing partner in the zodiac—give without losing yourself. "
            "Your vulnerability, when shared safely, is your greatest gift in love."
        ),
        "spiritual": (
            "Cancer's spiritual path runs through devotion (bhakti) to the Divine Mother. "
            "Honoring ancestors, caring for home as sacred space, and offering to the Moon on Purnima "
            "are powerful practices for your deeply intuitive soul."
        ),
        "planetary": (
            "The Moon governs your emotional tides. When the Moon transits favorably, you feel secure and creative. "
            "During challenging lunar phases, cultivate stillness and self-care rather than reacting from emotion."
        ),
        "nakshatra": (
            "Punarvasu, Pushya, and Ashlesha fall in Cancer. Pushya is the most auspicious nakshatra—"
            "if born here, you carry extraordinary capacity for nurturing, wisdom, and spiritual grace."
        ),
    },
    "Leo": {
        "career": (
            "Leo, ruled by the Sun, is born to lead, create, and inspire. "
            "Entertainment, management, politics, and education are your natural domains. "
            "The world needs your light—step into leadership positions with confidence and generosity."
        ),
        "love": (
            "Leo loves dramatically and loyally. You shower your partner with affection and expect appreciation in return. "
            "The key is remembering that love is not a performance—your authentic heart is more beautiful than any grand gesture."
        ),
        "spiritual": (
            "The Sun is the symbol of the Atman—the eternal self. Leo's spiritual path is heart-centered: "
            "service, creative devotion, and radiating warmth to all who cross your path. "
            "Gayatri Mantra practice connects you to your solar essence."
        ),
        "planetary": (
            "The Sun rules your vitality, ego, and life purpose. Strong Sun transits bring recognition, "
            "leadership opportunities, and creative breakthroughs. Honor Surya with morning Namaskar and gratitude practice."
        ),
        "nakshatra": (
            "Magha, Purva Phalguni, and Uttara Phalguni fall in Leo—royal, artistic, and responsible energies. "
            "Magha especially connects to ancestral power and the soul's regal heritage."
        ),
    },
    "Virgo": {
        "career": (
            "Virgo's Mercury-ruled precision and service orientation shine in medicine, research, data science, "
            "writing, and healthcare. Your analytical gifts are extraordinary. "
            "Pair your precision with self-compassion—perfection is a direction, not a destination."
        ),
        "love": (
            "Virgo expresses love through devoted acts of service and practical care. "
            "You notice every detail of your partner's wellbeing. Work on voicing appreciation—"
            "your love, when spoken, is as beautiful as it is when shown."
        ),
        "spiritual": (
            "Seva—selfless service—is Virgo's highest spiritual practice. "
            "Yoga, Ayurveda, and the study of sacred texts align with your love of precise knowledge. "
            "The discriminating intellect, purified through practice, becomes spiritual discernment."
        ),
        "planetary": (
            "Mercury rules your intellect and analytical power. Virgo is Mercury's exaltation sign—"
            "your mental gifts are exceptional. Use them in service of genuine understanding, not just criticism."
        ),
        "nakshatra": (
            "Uttara Phalguni, Hasta, and Chitra fall in Virgo—responsibility, skilled hands, and creative brilliance. "
            "Hasta natives especially are gifted healers and craftspeople."
        ),
    },
    "Libra": {
        "career": (
            "Libra's Venus-ruled diplomatic intelligence and aesthetic sense shine in law, design, human resources, "
            "counseling, and the arts. You are a natural bridge-builder. "
            "Trust your instincts about fairness—they are rarely wrong."
        ),
        "love": (
            "Partnership is the center of Libra's universe. You are romantic, attentive, and deeply committed to harmony. "
            "Learn to voice your own needs—a truly balanced relationship has two equal voices."
        ),
        "spiritual": (
            "Beauty and justice are Libra's spiritual callings. Venus's higher octave is devotional love. "
            "Art made as offering, relationships treated as sacred—these are your temples. "
            "Balance your active social life with periods of reflective solitude."
        ),
        "planetary": (
            "Venus and Saturn both grace Libra—Venus with beauty and love, Saturn with wisdom and justice (Saturn is exalted in Libra). "
            "This combination, when integrated, produces rare individuals who balance beauty with responsibility."
        ),
        "nakshatra": (
            "Chitra, Swati, and Vishakha fall in Libra—creative brilliance, independence, and determined purpose. "
            "Vishakha's dual influence (Libra/Scorpio) signals a crossroads soul, choosing between pleasure and depth."
        ),
    },
    "Scorpio": {
        "career": (
            "Scorpio's Pluto and Mars energy brings extraordinary depth and determination to whatever they pursue. "
            "Psychology, research, investigation, surgery, and finance suit you powerfully. "
            "Your stamina and insight are unmatched—trust the process even when results take time."
        ),
        "love": (
            "Scorpio loves with terrifying intensity and absolute loyalty. You seek total merger, not surface connection. "
            "The invitation is to love deeply without trying to possess. "
            "Vulnerability, not control, is what creates the profound intimacy you crave."
        ),
        "spiritual": (
            "Scorpio's path runs through the underworld—shadow work, transformation, and emergence stronger. "
            "Pluto is the Moksha-karaka of Western astrology; Ketu performs this function in Vedic astrology. "
            "Kundalini practices, deep meditation, and fearless self-inquiry are your sadhana."
        ),
        "planetary": (
            "Mars and Pluto co-rule Scorpio, giving you intense energy and transformative power. "
            "When Mars transits strongly, your ambition and physical stamina peak. "
            "Work with this energy consciously—it can heal or wound depending on intention."
        ),
        "nakshatra": (
            "Vishakha, Anuradha, and Jyeshtha fall in Scorpio—purposeful, devoted, and powerful. "
            "Jyeshtha, governed by Mercury and Indra, bestows natural authority and protective strength."
        ),
    },
    "Sagittarius": {
        "career": (
            "Jupiter-ruled Sagittarius thrives in academia, law, international business, publishing, philosophy, and travel. "
            "Your expansive vision and natural optimism inspire those around you. "
            "Channel your enthusiasm into focused mastery—depth complements your natural breadth."
        ),
        "love": (
            "Sagittarius needs a partner who is also a companion for adventures of mind and spirit. "
            "You are honest, generous, and deeply loving—sometimes tactlessly so. "
            "Commitment is possible when you find someone who expands rather than limits your world."
        ),
        "spiritual": (
            "Sagittarius is the natural philosopher-pilgrim of the zodiac. Jupiter's wisdom guides your search for Truth. "
            "World religions, pilgrimage, and teaching are your spiritual domains. "
            "Every journey—inner or outer—is a sacred quest."
        ),
        "planetary": (
            "Jupiter is your ruling planet—the great benefic, the divine teacher. "
            "Jupiter's transits bring expansion, wisdom, and abundance. "
            "Honor Guru through study, generosity, and reverence for teachers and elders."
        ),
        "nakshatra": (
            "Mula, Purva Ashadha, and Uttara Ashadha fall in Sagittarius—rootedness, invincibility, and righteous victory. "
            "Mula, ruled by Ketu, demands going to the root of all things: the seeker's ultimate nakshatra."
        ),
    },
    "Capricorn": {
        "career": (
            "Saturn-ruled Capricorn is the architect of the zodiac—patient, disciplined, and built for long-term success. "
            "Business, government, engineering, and finance reward your sustained effort. "
            "Saturn's greatest gift is this: the longer you build, the more enduring the achievement."
        ),
        "love": (
            "Capricorn takes love seriously—as a commitment, not a casualty of ambition. "
            "You show love through reliability and provision. "
            "Open your emotional interior to your partner; the warmth beneath your composed exterior is deeply beautiful."
        ),
        "spiritual": (
            "Saturn teaches karma yoga—disciplined action without grasping results. "
            "Your structured approach to practice, honoring tradition and elders, and steadfast seva "
            "build spiritual capital slowly but absolutely. Saturn's slowness is its grace."
        ),
        "planetary": (
            "Saturn governs karma, discipline, and long-term structures. Shani's transits test patience and reveal what is truly built to last. "
            "Honor Saturn through Saturday fasting, selfless service, and visiting Shani temples."
        ),
        "nakshatra": (
            "Uttara Ashadha, Shravana, and Dhanishtha fall in Capricorn—righteous victory, sacred listening, and rhythmic abundance. "
            "Shravana natives are lifelong learners who transmit wisdom through teaching and counseling."
        ),
    },
    "Aquarius": {
        "career": (
            "Aquarius, ruled by Saturn and Uranus, pioneers the future. Technology, science, social reform, "
            "and humanitarian work are your natural domains. "
            "Your unconventional thinking is not a liability—it is the innovation the world needs."
        ),
        "love": (
            "Aquarius needs intellectual connection and shared vision before romantic depth can develop. "
            "You love humanity broadly; the invitation is to love one person specifically and consistently. "
            "A partner who is also your best friend and fellow idealist is your match."
        ),
        "spiritual": (
            "Aquarius transcends individual ego toward collective consciousness. "
            "Energy healing, group meditation, and work for the collective good are your spiritual practices. "
            "Uranus awakens; your spiritual path is revolutionary by nature."
        ),
        "planetary": (
            "Saturn disciplines and Uranus liberates—together, they make Aquarius both responsible and revolutionary. "
            "Saturn's structure grounds Uranian genius. Honor both by combining disciplined practice with open-minded innovation."
        ),
        "nakshatra": (
            "Dhanishtha, Shatabhisha, and Purva Bhadrapada fall in Aquarius—rhythm, healing mystery, and transformative vision. "
            "Shatabhisha, ruled by Rahu and Varuna, makes gifted healers and keepers of secret knowledge."
        ),
    },
    "Pisces": {
        "career": (
            "Jupiter and Neptune bless Pisces with imagination, compassion, and spiritual attunement. "
            "Arts, music, healing, psychology, and spiritual work are your natural vocations. "
            "Your gift is the ability to hold space for the full spectrum of human experience."
        ),
        "love": (
            "Pisces is the most romantically selfless sign. You dissolve boundaries in love—beautiful but requiring discernment. "
            "Seek a partner who cherishes your sensitivity rather than exploiting it. "
            "Your capacity for unconditional love is the zodiac's rarest gift."
        ),
        "spiritual": (
            "Pisces lives at the threshold between the seen and unseen worlds. "
            "Surrender, devotion (bhakti), and mystical practice are your spiritual home. "
            "Neptune dissolves the ego gently; your path leads naturally toward liberation."
        ),
        "planetary": (
            "Jupiter and Neptune co-rule Pisces—wisdom and mysticism, expansion and dissolution. "
            "Jupiter's transits bring spiritual grace and abundance. Neptune dissolves limitations. "
            "Honor Jupiter through gratitude, generosity, and reverence for the sacred in all things."
        ),
        "nakshatra": (
            "Uttara Bhadrapada, Revati, and Purva Bhadrapada (partially) fall in Pisces—wisdom, wholeness, and transformative vision. "
            "Revati is the final nakshatra—completion, compassion, and the guardian who brings all souls safely home."
        ),
    },
}

# Hindi stub responses (Devanagari)
_STUB_HI = {
    "Aries": {
        "career": (
            "मेष राशि वाले जातकों के लिए मंगल ग्रह ऊर्जा और साहस का स्रोत है। "
            "उद्यमिता, नेतृत्व, खेल, और सैन्य क्षेत्र में आपकी प्रतिभा चमकती है। "
            "निर्णायक कदम उठाएँ और अपनी प्राकृतिक नेतृत्व क्षमता पर भरोसा रखें।"
        ),
        "love": (
            "मेष राशि में प्रेम जोशीला और सीधा होता है। आपको एक ऐसे साथी की आवश्यकता है "
            "जो आपकी ऊर्जा के साथ कदम से कदम मिला सके। धैर्य रखें—प्रेम गहरा होता है।"
        ),
        "spiritual": (
            "मेष जातकों के लिए कर्मयोग सबसे उपयुक्त साधना है। सूर्य नमस्कार और "
            "मंत्र जप से मंगल की ऊर्जा को आध्यात्मिक मार्ग पर लगाएँ।"
        ),
        "planetary": (
            "मंगल आपका स्वामी ग्रह है—साहस, शक्ति और महत्वाकांक्षा का प्रतीक। "
            "मंगल के अनुकूल गोचर में नए कार्य आरम्भ करें।"
        ),
        "nakshatra": (
            "अश्विनी, भरणी और कृत्तिका—मेष के तीन नक्षत्र—गति, परिवर्तन और "
            "अग्नि की शक्ति प्रदान करते हैं। आपका जन्म नक्षत्र आत्मा की गहरी पुकार बताता है।"
        ),
    },
    "Taurus": {
        "career": "वृष राशि के जातक वित्त, संपत्ति, संगीत और कला में उत्कृष्ट होते हैं। धैर्य और निष्ठा आपकी पेशेवर शक्ति है।",
        "love": "वृष राशि में प्रेम गहरा और समर्पित होता है। शुक्र की कृपा से आपका प्रेम जीवन सुंदर और स्थायी होगा।",
        "spiritual": "प्रकृति में बैठना, संगीत और मंत्र साधना वृष के लिए आध्यात्मिक द्वार खोलती है।",
        "planetary": "शुक्र आपका स्वामी है। शुक्रवार का व्रत और लक्ष्मी स्तोत्र का पाठ लाभकारी है।",
        "nakshatra": "रोहिणी नक्षत्र—चंद्रमा का सर्वप्रिय नक्षत्र—वृष राशि में पड़ता है और अपार सौंदर्य तथा समृद्धि देता है।",
    },
    "Gemini": {
        "career": "मिथुन राशि के जातक पत्रकारिता, तकनीक, शिक्षण और व्यापार में चमकते हैं। बुध की बुद्धि आपकी सबसे बड़ी शक्ति है।",
        "love": "मिथुन के लिए मानसिक जुड़ाव प्रेम की नींव है। एक बौद्धिक साथी आपके जीवन को पूर्ण करता है।",
        "spiritual": "मौन ध्यान और पवित्र ग्रंथों का अध्ययन मिथुन जातकों के लिए आत्म-साक्षात्कार का मार्ग है।",
        "planetary": "बुध आपका स्वामी ग्रह है—संचार और विश्लेषण में आप निपुण हैं।",
        "nakshatra": "मृगशिरा, आर्द्रा और पुनर्वसु मिथुन के नक्षत्र हैं—खोज, परिवर्तन और प्रकाश की वापसी।",
    },
    "Cancer": {
        "career": "कर्क राशि के जातक स्वास्थ्य, शिक्षा और सेवा क्षेत्र में श्रेष्ठ होते हैं।",
        "love": "कर्क राशि में प्रेम गहरा, समर्पित और सुरक्षात्मक होता है। भावनात्मक सुरक्षा आपके लिए अनिवार्य है।",
        "spiritual": "माँ की भक्ति और पूर्णिमा को चंद्रमा को जल अर्पण कर्क जातकों के लिए सबसे शक्तिशाली साधना है।",
        "planetary": "चंद्रमा आपका स्वामी है—मन और भावनाओं का राजा। सोमवार का व्रत और 'ॐ चंद्राय नमः' मंत्र लाभदायक है।",
        "nakshatra": "पुनर्वसु, पुष्य और आश्लेषा कर्क के नक्षत्र हैं। पुष्य सर्वाधिक शुभ नक्षत्र माना जाता है।",
    },
    "Leo": {
        "career": "सिंह राशि के जातक नेतृत्व, मनोरंजन और राजनीति में स्वाभाविक रूप से चमकते हैं।",
        "love": "सिंह राशि में प्रेम भव्य और निष्ठावान होता है। अपने साथी की सराहना करें और उनसे सराहना पाएँ।",
        "spiritual": "सूर्य आत्मा का प्रतीक है। गायत्री मंत्र और सूर्य नमस्कार सिंह की आत्मा को जागृत करते हैं।",
        "planetary": "सूर्य आपका स्वामी है—आत्मबल और पहचान का स्रोत। सूर्योदय पर जल अर्पण और गायत्री जप शक्तिवर्धक हैं।",
        "nakshatra": "मघा, पूर्व फाल्गुनी और उत्तर फाल्गुनी सिंह के नक्षत्र हैं—राजसी, कलात्मक और जिम्मेदार।",
    },
    "Virgo": {
        "career": "कन्या राशि के जातक चिकित्सा, अनुसंधान और सेवा क्षेत्र में अत्यंत कुशल होते हैं।",
        "love": "कन्या राशि में प्रेम सेवा और समर्पण के रूप में व्यक्त होता है। अपनी भावनाएँ शब्दों में भी व्यक्त करें।",
        "spiritual": "सेवा (सेवा) कन्या की सर्वोच्च साधना है। योग, आयुर्वेद और ग्रंथ अध्ययन आत्मिक विकास का मार्ग है।",
        "planetary": "बुध कन्या में उच्च का होता है—आपकी बौद्धिक क्षमता असाधारण है।",
        "nakshatra": "उत्तर फाल्गुनी, हस्त और चित्रा कन्या के नक्षत्र हैं—कुशल हाथ और रचनात्मक प्रतिभा के स्वामी।",
    },
    "Libra": {
        "career": "तुला राशि के जातक कानून, डिज़ाइन और कूटनीति में प्रतिभाशाली होते हैं।",
        "love": "तुला के लिए साझेदारी जीवन का केंद्र है। संतुलन और न्याय के साथ प्रेम का पोषण करें।",
        "spiritual": "सौंदर्य और न्याय तुला के आध्यात्मिक आह्वान हैं। भक्ति और कलात्मक साधना आपके लिए उपयुक्त है।",
        "planetary": "शुक्र और शनि दोनों तुला को प्रभावित करते हैं—सौंदर्य और जिम्मेदारी का दुर्लभ संयोग।",
        "nakshatra": "चित्रा, स्वाती और विशाखा तुला के नक्षत्र हैं—रचनात्मकता, स्वतंत्रता और दृढ़ संकल्प।",
    },
    "Scorpio": {
        "career": "वृश्चिक राशि के जातक मनोविज्ञान, अनुसंधान और वित्त में असाधारण गहराई रखते हैं।",
        "love": "वृश्चिक में प्रेम गहन और पूर्ण समर्पण की माँग करता है। नियंत्रण नहीं, विश्वास—यही प्रेम की कुंजी है।",
        "spiritual": "कुंडलिनी साधना, ध्यान और आत्म-परीक्षण वृश्चिक का आध्यात्मिक मार्ग है।",
        "planetary": "मंगल और प्लूटो वृश्चिक को नियंत्रित करते हैं—परिवर्तन की असाधारण शक्ति आपके भीतर है।",
        "nakshatra": "विशाखा, अनुराधा और ज्येष्ठा वृश्चिक के नक्षत्र हैं—उद्देश्य, भक्ति और सत्ता।",
    },
    "Sagittarius": {
        "career": "धनु राशि के जातक शिक्षा, कानून और अंतर्राष्ट्रीय व्यापार में स्वाभाविक रूप से उत्कृष्ट होते हैं।",
        "love": "धनु के लिए साथी एक यात्रा-साथी होना चाहिए—मन और आत्मा की यात्रा में।",
        "spiritual": "तीर्थयात्रा, दर्शन और सत्य की खोज धनु का आध्यात्मिक स्वभाव है। गुरु की कृपा से ज्ञान प्रकट होता है।",
        "planetary": "गुरु आपका स्वामी है—ज्ञान, विस्तार और आशीर्वाद का स्रोत। गुरुवार का व्रत और गुरु मंत्र जप लाभकारी है।",
        "nakshatra": "मूल, पूर्वाषाढ़ा और उत्तराषाढ़ा धनु के नक्षत्र हैं—जड़ों की खोज, अपराजेयता और धर्म की विजय।",
    },
    "Capricorn": {
        "career": "मकर राशि के जातक व्यवसाय, सरकार और इंजीनियरिंग में दीर्घकालिक सफलता पाते हैं।",
        "love": "मकर में प्रेम गंभीर और दीर्घकालिक प्रतिबद्धता के रूप में व्यक्त होता है। अपने हृदय को खोलें।",
        "spiritual": "शनि कर्मयोग सिखाता है—फल की चिंता किए बिना कर्म करना। सेवा और अनुशासन मकर की साधना है।",
        "planetary": "शनि अनुशासन और कर्म का ग्रह है। शनिवार का व्रत और शनि स्तोत्र का पाठ करें।",
        "nakshatra": "उत्तराषाढ़ा, श्रवण और धनिष्ठा मकर के नक्षत्र हैं—धर्म की विजय, पवित्र श्रवण और लयबद्ध समृद्धि।",
    },
    "Aquarius": {
        "career": "कुंभ राशि के जातक प्रौद्योगिकी, विज्ञान और सामाजिक सुधार में अग्रणी होते हैं।",
        "love": "कुंभ के लिए एक मित्र जो प्रेमी भी हो—यही आदर्श साथी है। बौद्धिक और आदर्शवादी जुड़ाव अनिवार्य है।",
        "spiritual": "सामूहिक चेतना और ऊर्जा उपचार कुंभ का आध्यात्मिक मार्ग है। समूह ध्यान विशेष रूप से प्रभावशाली है।",
        "planetary": "शनि और यूरेनस दोनों कुंभ को प्रभावित करते हैं—अनुशासन और क्रांति का अद्भुत संयोग।",
        "nakshatra": "धनिष्ठा, शतभिषा और पूर्व भाद्रपद कुंभ के नक्षत्र हैं—लय, रहस्यमय उपचार और परिवर्तनकारी दृष्टि।",
    },
    "Pisces": {
        "career": "मीन राशि के जातक कला, संगीत, उपचार और आध्यात्मिक कार्य में अतुलनीय हैं।",
        "love": "मीन राशि में प्रेम असीम और आत्मिक होता है। अपनी संवेदनशीलता की रक्षा करते हुए प्रेम करें।",
        "spiritual": "समर्पण और भक्ति मीन का स्वाभाविक आध्यात्मिक मार्ग है। ध्यान और भजन-कीर्तन आत्मा को मुक्त करते हैं।",
        "planetary": "गुरु और नेप्च्यून मीन को नियंत्रित करते हैं—ज्ञान और रहस्यवाद का दिव्य संयोग।",
        "nakshatra": "उत्तर भाद्रपद, रेवती और पूर्व भाद्रपद (आंशिक) मीन के नक्षत्र हैं—ज्ञान, पूर्णता और करुणा।",
    },
}

_FALLBACK_EN = (
    "I'd be happy to offer Vedic astrology guidance. Could you share your birth date so I can provide "
    "personalized insights based on your zodiac sign and planetary influences?"
)

_FALLBACK_HI = (
    "मैं आपको वैदिक ज्योतिष के आधार पर मार्गदर्शन देना चाहूँगा। "
    "कृपया अपनी जन्म तिथि साझा करें ताकि मैं व्यक्तिगत ज्ञान प्रदान कर सकूँ।"
)


class BaseLLMClient(ABC):
    @abstractmethod
    async def complete(self, messages: List[dict]) -> str:
        ...


class StubLLMClient(BaseLLMClient):
    """Returns hand-written responses when no OpenAI key is configured."""

    async def complete(self, messages: List[dict]) -> str:
        system = next((m["content"] for m in messages if m["role"] == "system"), "")
        user_msg = next((m["content"] for m in messages if m["role"] == "user"), "")
        language = "hi" if "हिंदी" in system or "Devanagari" in system else "en"

        # Extract zodiac from system prompt — look for the specific marker line
        zodiac = None
        for sign in _STUB_EN:
            if f"Sun sign (zodiac) is {sign}" in system:
                zodiac = sign
                break

        # Determine intent from user message
        intent = "career"
        msg_lower = user_msg.lower()
        if any(w in msg_lower for w in ["love", "relation", "marriage", "partner", "romance"]):
            intent = "love"
        elif any(w in msg_lower for w in ["spirit", "karma", "dharma", "meditat", "yoga", "moksha"]):
            intent = "spiritual"
        elif any(w in msg_lower for w in ["planet", "saturn", "jupiter", "mars", "venus", "transit", "dasha"]):
            intent = "planetary"
        elif any(w in msg_lower for w in ["nakshatra", "star", "lunar"]):
            intent = "nakshatra"

        stub_map = _STUB_HI if language == "hi" else _STUB_EN
        if zodiac and zodiac in stub_map and intent in stub_map[zodiac]:
            return stub_map[zodiac][intent]

        return _FALLBACK_HI if language == "hi" else _FALLBACK_EN


class OpenAIClient(BaseLLMClient):
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo"):
        from openai import AsyncOpenAI
        self._client = AsyncOpenAI(api_key=api_key)
        self._model = model

    async def complete(self, messages: List[dict]) -> str:
        for attempt in range(2):
            try:
                resp = await self._client.chat.completions.create(
                    model=self._model,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=600,
                )
                return resp.choices[0].message.content.strip()
            except Exception as exc:
                if attempt == 0 and "rate_limit" in str(exc).lower():
                    await asyncio.sleep(2)
                    continue
                logger.error("OpenAI completion failed: %s", exc)
                raise


@lru_cache
def get_llm_client() -> BaseLLMClient:
    from app.core.config import get_settings
    settings = get_settings()
    if settings.openai_api_key:
        logger.info("Using OpenAI LLM client (model=%s)", settings.openai_model)
        return OpenAIClient(api_key=settings.openai_api_key, model=settings.openai_model)
    logger.info("No OPENAI_API_KEY found — using StubLLMClient")
    return StubLLMClient()
