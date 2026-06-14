
test_cases = [

    # ── Routes & Access ──────────────────────────────────
    {
        "question": "What are the routes to visit Kailash Mansarovar?",
        "ground_truth": "The routes to Kailash Mansarovar are from Kathmandu in Nepal, from Lucknow in India, and from Lhasa in Tibet. The Ministry of Tourism India has identified two routes: through Lipulekh Pass in Uttarakhand and through Nathu-La Pass in Sikkim."
    },
    {
        "question": "Which route is considered the least complex to reach Kailash Mansarovar?",
        "ground_truth": "The most favoured and less complex routes are from Kathmandu in Nepal, from Lucknow in India, and from Lhasa in Tibet."
    },
    {
        "question": "What are the two routes identified by Ministry of Tourism India for Kailash Mansarovar Yatra?",
        "ground_truth": "The Ministry of Tourism India identified two routes: through Lipulekh Pass in Uttarakhand and through Nathu-La Pass in Sikkim."
    },

    # ── Geography & Location ─────────────────────────────
    {
        "question": "What is the elevation of Lake Mansarovar?",
        "ground_truth": "Lake Mansarovar is situated at an elevation of 4,590 meters."
    },
    {
        "question": "What is the elevation of Mount Kailash?",
        "ground_truth": "Mount Kailash stands at an elevation of 6638 meters or 21778 feet."
    },
    {
        "question": "Where is Mount Kailash located?",
        "ground_truth": "Mount Kailash is situated in the Kailash Range also known as Gangdise Mountains of the Transhimalaya in the Tibet Autonomous Region in China."
    },
    {
        "question": "What is the area of Lake Mansarovar?",
        "ground_truth": "Lake Mansarovar extends across an area of approximately 412 square kilometres."
    },
    {
        "question": "What are the rivers that originate from Lake Mansarovar?",
        "ground_truth": "Asia's four greatest rivers originate from Lake Mansarovar: the Ghaghara, Brahmaputra, Sutlej and Sindhu."
    },

    # ── Famous Places ────────────────────────────────────
    {
        "question": "What are the famous places near Kailash Mansarovar?",
        "ground_truth": "The famous places near Kailash Mansarovar are Mount Kailash, Ashtapad, Lake Mansarovar, Gauri Kund, Rakshas Taal, and Yam Dwar."
    },
    {
        "question": "How many Buddhist monasteries are on the shores of Lake Mansarovar?",
        "ground_truth": "There are five Buddhist monasteries on the shores of Lake Mansarovar: Chiu on the northwest shore, Gossul, Seralung, Yerngo and Trugo."
    },

    # ── Trekking & Parikrama ─────────────────────────────
    {
        "question": "How long is the parikrama of Mount Kailash?",
        "ground_truth": "The parikrama of Mount Kailash is about 52 km or 32 miles long, out of which about 9 km is done by vehicle. It takes three days of trekking."
    },
    {
        "question": "In which direction is the parikrama of Mount Kailash done?",
        "ground_truth": "The parikrama of Mount Kailash is done in a clockwise direction."
    },
    {
        "question": "What is the highest point crossed during the Kailash parikrama?",
        "ground_truth": "The highest point crossed during the parikrama is the Dolma La pass at 18,200 feet or 5,600 meters."
    },
    {
        "question": "Where do pilgrims encamp during the Kailash parikrama?",
        "ground_truth": "Pilgrims encamp for two nights during the parikrama — first near the meadow of Dirapuk Gompa and second at Zuthulpukh."
    },
    {
        "question": "How long is the parikrama of Lake Mansarovar?",
        "ground_truth": "The parikrama of Lake Mansarovar is about 82 kilometers or 51 miles."
    },

    # ── Weather ──────────────────────────────────────────
    {
        "question": "What is the weather like in the TAR region?",
        "ground_truth": "TAR has a harsh climate. In winter temperatures go below minus 16 degrees Celsius and in summer above 29 degrees Celsius. It is a highly dry region with thin air due to high elevation."
    },
    {
        "question": "What is the minimum temperature in TAR during winter?",
        "ground_truth": "During wintertime the temperature in TAR goes below minus 16 degrees Celsius."
    },

    # ── Eligibility & Documents ──────────────────────────
    {
        "question": "Who can travel to Kailash Mansarovar?",
        "ground_truth": "Any person in good health who can undertake travel at high altitude of 5600 meters and above can apply. The age limit to obtain permit is 70 years. A doctor's certificate confirming fitness is required."
    },
    {
        "question": "What documents are required for Kailash Yatra?",
        "ground_truth": "A valid passport, Tibet visa, and necessary permits are mandatory. Indian nationals must present passports to the China Embassy in Delhi along with a copy of the permit to get group visa. A doctor's fitness certificate is also required."
    },
    {
        "question": "What is the age limit to obtain permit for Kailash Mansarovar Yatra?",
        "ground_truth": "The age limit to obtain permit for Kailash Mansarovar Yatra is 70 years."
    },
    {
        "question": "Can Indian nationals travel to Nepal without a passport?",
        "ground_truth": "Indian passports can fly to Nepal either with a valid passport or Indian Voter ID Card. No other document is accepted by immigration at Indian airports for outbound flights to Nepal."
    },

    # ── Tour Packages ────────────────────────────────────
    {
        "question": "What are the tour package options available for Kailash Mansarovar Yatra?",
        "ground_truth": "There are 5 package options: 9 days by helicopter from Lucknow, 11 days by helicopter from Kathmandu, 14 days by road from Kathmandu, 15 days by road from Lhasa Tibet, and 19 days Inner Kora from Kathmandu."
    },
    {
        "question": "What is the shortest package available for Kailash Mansarovar Yatra?",
        "ground_truth": "The shortest package is 9 days and 8 nights by helicopter from Lucknow."
    },
    {
        "question": "Which package covers the complete Inner and Outer Kora of Mount Kailash?",
        "ground_truth": "Package Option 5 — 19 days and 18 nights Inner Kora from Kathmandu covers the complete outer and inner Kora or Parikrama of Mount Kailash."
    },

    # ── Religious Significance ───────────────────────────
    {
        "question": "What is the religious significance of Mount Kailash for Hindus?",
        "ground_truth": "According to Hinduism Mount Kailash is considered the heavenly abode of Lord Shiva. The Vishnu Purana states the four faces of Mount Kailash are made of crystal, ruby, gold, and lapis lazuli. It is said to be a pillar of the world located at the heart of six mountain ranges symbolizing a lotus."
    },
    {
        "question": "What is the significance of Mount Kailash for Jains?",
        "ground_truth": "For Jainism, Kailash is also known as Meru Parvat or Sumeru. Ashtapada, the mountain next to Mount Kailash, is the site where the first Jain Tirthankara Rishabhadeva attained Nirvana or Moksha."
    },
    {
        "question": "What religions consider Kailash Mansarovar sacred?",
        "ground_truth": "Kailash Mansarovar is sacred to Hindus, Jains, Buddhists, and the Bon Po religion."
    },

    # ── Risks & Challenges ───────────────────────────────
    {
        "question": "What are the risks involved in Kailash Mansarovar Yatra?",
        "ground_truth": "Risks include difficulty getting travel permits and group visa, unpredictable weather causing delays, altitude sickness, limited infrastructure and services in Tibet, and basic accommodation conditions. Trekking requires extraordinary mental and physical strength."
    },
    {
        "question": "What health precaution is needed for Kailash Yatra?",
        "ground_truth": "Every pilgrim must consult a doctor and undergo basic medical tests to ensure fitness for high altitude travel. A doctor's certificate confirming fitness is required before commencing the yatra."
    },
    {
        "question": "What age group may be stopped from performing parikrama?",
        "ground_truth": "Tibetan authorities sometimes stop people above 60 years of age from undertaking the parikrama due to health and adverse climatic conditions."
    },

    # ── People & Language ────────────────────────────────
    {
        "question": "What languages are spoken in the Tibet Autonomous Region?",
        "ground_truth": "The official language in Tibet Autonomous Region is Standard Tibetan. People also speak Chinese and Nepalese, and the majority of the population is fluent in English."
    },
    {
        "question": "Who are the people living near Mount Kailash?",
        "ground_truth": "The people living in the Tibet Autonomous Region near Mount Kailash are Tibetans who cover more than 90 percent of the population, along with Chinese and Nepalis."
    },
]
