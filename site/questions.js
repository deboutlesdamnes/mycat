// Simulated misconception quiz questions (placeholder content standing in
// for real output of the writer/critic scraping pipeline in ../main.py).
const QUESTIONS = [
  {
    question: "Cats always land on their feet, no matter what.",
    options: ["True — it's a guaranteed reflex", "Mostly true, but it can fail", "False — it's a total myth", "Only kittens can do it"],
    correct: 1,
    explanation: "The 'righting reflex' lets most cats reorient mid-fall, but it needs enough height and time to work, and it isn't guaranteed. Very short falls, injury, illness, or age can all cause a cat to land badly — 'high-rise syndrome' in vet medicine is a real, sometimes serious injury pattern."
  },
  {
    question: "Goldfish have a memory span of only a few seconds.",
    options: ["True", "False — it's actually months", "False — it's about 24 hours", "True, but only in captivity"],
    correct: 1,
    explanation: "Studies show goldfish can learn to navigate mazes and recognize feeding schedules, retaining information for months, not seconds. The '3-second memory' idea is a popular myth with no scientific basis."
  },
  {
    question: "Humans only use 10% of their brains.",
    options: ["True", "False — nearly all of the brain is active over a day", "True, except for geniuses", "False — it's closer to 50%"],
    correct: 1,
    explanation: "Brain imaging shows virtually all regions of the brain have identifiable functions and are active at various points, even during sleep. The '10%' claim has no basis in neuroscience."
  },
  {
    question: "Cats are completely colorblind and see only in black and white.",
    options: ["True", "False — they see a limited color range", "True, except for Siamese cats", "False — they see the same colors as humans"],
    correct: 1,
    explanation: "Cats have fewer cone cells than humans, so their color range is more limited (similar to red-green colorblindness in people), but they do perceive some color — mainly blues and yellows — not just grayscale."
  },
  {
    question: "Bulls become enraged at the color red.",
    options: ["True", "False — bulls are colorblind to red; it's the motion that provokes them", "True, but only during mating season", "False — it's the smell of the cape"],
    correct: 1,
    explanation: "Cattle lack the receptor needed to distinguish red from other colors well. What actually provokes a bull in a bullfight is the movement and flapping of the cape, not its color."
  },
  {
    question: "Napoleon Bonaparte was unusually short for his time.",
    options: ["True, he was under 5 feet tall", "False — he was about average height for a Frenchman of his era", "True, he was a dwarf by modern standards", "False — he was unusually tall"],
    correct: 1,
    explanation: "Napoleon was about 5'6\"-5'7\" (around 170 cm), close to average French male height at the time. The 'short' myth stems partly from confusion between French and English measurement units, and partly from British political cartoons."
  },
  {
    question: "Cats purr only when they are happy or content.",
    options: ["True", "False — they also purr when stressed, injured, or dying", "True, purring is always a sign of contentment", "False — purring only happens during sleep"],
    correct: 1,
    explanation: "Cats purr in a variety of states, including pain, fear, and even near death. One theory is that the vibration frequency of purring may promote healing and self-soothing, not just express contentment."
  },
  {
    question: "Lightning never strikes the same place twice.",
    options: ["True", "False — tall or exposed structures get struck repeatedly", "True, except during hurricanes", "False — it only strikes flat ground twice"],
    correct: 1,
    explanation: "Lightning is drawn to tall, conductive, or exposed points. Structures like the Empire State Building are struck dozens of times a year — location and height matter far more than any 'one strike per spot' rule."
  },
  {
    question: "Great Wall of China is the only man-made structure visible from space with the naked eye.",
    options: ["True", "False — it's barely visible even from low orbit, and other structures are more visible", "True, but only at night", "False — it's visible only from the Moon"],
    correct: 1,
    explanation: "Astronauts have reported the Great Wall is actually difficult to see from low Earth orbit without aid because it's narrow and blends with its surroundings. Highways, airports, and city lights are often more visible."
  },
  {
    question: "A cat's whiskers are just decorative fur.",
    options: ["True", "False — they're touch-sensitive sensory organs", "True, only kittens' whiskers serve a purpose", "False — they're used only for balance"],
    correct: 1,
    explanation: "Whiskers (vibrissae) are deeply rooted, richly innervated sensory organs that help cats judge spaces, detect nearby movement, and navigate in the dark — far more than decoration."
  },
  {
    question: "Vikings wore horned helmets into battle.",
    options: ["True", "False — no archaeological evidence supports this", "True, but only their chiefs did", "False — they wore feathered helmets instead"],
    correct: 1,
    explanation: "No Viking-age helmet with horns has ever been found in the archaeological record. The horned-helmet image largely comes from 19th-century opera costumes and Romantic-era art."
  },
  {
    question: "Cracking your knuckles causes arthritis.",
    options: ["True", "False — studies find no link to arthritis", "True, but only after age 40", "False — it strengthens the joints instead"],
    correct: 1,
    explanation: "Multiple long-term studies, including one researcher who cracked only one hand's knuckles for decades, found no increased arthritis risk. The sound comes from gas bubbles collapsing in joint fluid, not joint damage."
  },
  {
    question: "Cats are naturally lactose tolerant and milk is a healthy treat for them.",
    options: ["True", "False — most adult cats are lactose intolerant", "True, only for kittens", "False — cats cannot digest any liquids besides water"],
    correct: 1,
    explanation: "Kittens produce lactase to digest their mother's milk, but most cats lose much of this enzyme after weaning. Cow's milk often causes digestive upset in adult cats, despite the popular image of cats loving a saucer of milk."
  },
  {
    question: "You lose most of your body heat through your head.",
    options: ["True — up to 80%", "False — heat loss is roughly proportional to exposed skin area", "True, but only in winter", "False — you lose heat only through your hands and feet"],
    correct: 1,
    explanation: "The '80% through your head' figure traces back to a flawed mid-20th-century military study where subjects wore full body suits but left only their heads exposed. Heat loss is roughly proportional to how much skin is uncovered, wherever it is."
  },
  {
    question: "Sushi means 'raw fish.'",
    options: ["True", "False — it refers to the vinegared rice", "True, but only in Japan", "False — it means 'fresh catch'"],
    correct: 1,
    explanation: "'Sushi' actually refers to the seasoned, vinegared rice used in the dish — not the fish. Many sushi styles use cooked seafood, vegetables, or no fish at all; 'sashimi' is the term for raw sliced fish on its own."
  }
];
