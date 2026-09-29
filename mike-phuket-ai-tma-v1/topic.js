(() => {
  const TOPICS = {
    eat: {
      title: "Где поесть",
      emoji: "🍜",
      intro: "",
      empty:
        "Пока нет партнёров по еде. Напиши Майку, подскажу где поесть рядом с тобой.",
      partners: [],
    },
    beaches: {
      title: "Пляжи",
      emoji: "🏖",
      intro: "",
      empty:
        "Пока нет партнёров по пляжам. Напиши Майку, подскажу куда ехать сегодня.",
      partners: [],
    },
    nearby: {
      title: "Что рядом",
      emoji: "📍",
      intro: "",
      empty:
        "Пока нет партнёров рядом. Напиши Майку район, скажу что вокруг.",
      partners: [],
    },
    money: {
      title: "Обмен Рублей",
      emoji: "💰",
      intro: "Вот партнёры для обмена рублей:",
      empty:
        "Пока нет доступных партнёров по обмену. Напиши Майку, подскажу что можно сделать.",
      partners: [
        {
          name: "Money Shop",
          blurb: "Сеть обменных офисов на Пхукете.",
          cta: "Обменять с Money Shop",
          logo: "./assets/partners/moneyshop.jpeg",
          fit: "contain",
          flag: "Майк рекомендует",
        },
        {
          name: "Ex24.pro",
          blurb:
            "Лицензированный обмен валюты. Таиланд, Вьетнам, ОАЭ, Китай, Бали. Переводы по всему миру.",
          cta: "Обменять с Ex24.pro",
          logo: "./assets/partners/ex24pro.png",
          fit: "contain",
        },
      ],
    },
    vehicle: {
      title: "Аренда транспорта",
      emoji: "🛵",
      intro: "Вот партнёры по аренде транспорта:",
      empty:
        "Пока нет доступных партнёров по аренде транспорта. Напиши Майку, подскажу что можно сделать.",
      partners: [
        {
          name: "Boomerang",
          blurb:
            "Надёжный сервис аренды автомобилей и мотобайков на Пхукете. Доставка по всему острову.",
          cta: "Арендовать у Boomerang",
          logo: "./assets/partners/boomerang.jpeg",
          fit: "contain",
        },
      ],
    },
    tours: {
      title: "Экскурсии",
      emoji: "🇹🇭",
      intro: "Вот партнёры по экскурсиям:",
      empty:
        "Пока нет доступных партнёров по экскурсиям. Напиши Майку, подскажу что можно сделать.",
      partners: [
        {
          name: "Остров Сокровищ",
          blurb:
            "С 2003 года в туризме. Авторские групповые и индивидуальные экскурсии.",
          cta: "Забронировать с Остров Сокровищ",
          logo: "./assets/partners/excursions.png",
          fit: "cover",
        },
      ],
    },
    esim: {
      title: "eSIM",
      emoji: "📱",
      intro: "Чтобы в любой стране оставаться на связи, можно купить eSIM здесь:",
      empty:
        "Пока нет доступного бота для покупки eSIM. Напиши Майку, подскажу что можно сделать.",
      partners: [
        {
          name: "Mike eSIM",
          blurb: "eSIM для поездок. Оставайся на связи в любой стране.",
          cta: "Купить eSIM",
          logo: "./assets/partners/esim.jpeg",
          fit: "cover",
        },
      ],
    },
    home: {
      title: "Недвижимость",
      emoji: "🏠",
      intro: "",
      empty:
        "Заявку по недвижимости принимает Майк. Напиши ему, задаст пару коротких вопросов.",
      partners: [],
    },
  };

  const params = new URLSearchParams(window.location.search);
  const topicId = params.get("id") || "";
  const topic = TOPICS[topicId];

  const titleEl = document.getElementById("topic-title");
  const emojiEl = document.getElementById("topic-emoji");
  const introEl = document.getElementById("topic-intro");
  const listEl = document.getElementById("partner-list");
  const emptyEl = document.getElementById("topic-empty");
  const emptyCopyEl = document.getElementById("topic-empty-copy");
  const toastEl = document.getElementById("toast");

  const tg = window.Telegram && window.Telegram.WebApp;
  if (tg) {
    tg.ready();
    tg.expand();
    tg.setHeaderColor("#F4F7FB");
    tg.setBackgroundColor("#F4F7FB");
  }

  if (!topic) {
    window.location.replace("./index.html");
    return;
  }

  document.title = `${topic.title} · Mike Phuket AI`;
  titleEl.textContent = topic.title;
  emojiEl.textContent = topic.emoji;
  emojiEl.setAttribute("data-topic", topicId);

  if (topic.intro) {
    introEl.hidden = false;
    introEl.textContent = topic.intro;
  }

  let toastTimer = 0;
  const showToast = (message) => {
    toastEl.textContent = message;
    toastEl.classList.add("is-on");
    window.clearTimeout(toastTimer);
    toastTimer = window.setTimeout(() => {
      toastEl.classList.remove("is-on");
    }, 2200);
  };

  const onStubClick = () => {
    showToast("Ссылка партнёра пока не открывается.");
  };

  if (!topic.partners.length) {
    emptyEl.hidden = false;
    emptyCopyEl.textContent = topic.empty;
    return;
  }

  topic.partners.forEach((partner) => {
    const item = document.createElement("li");
    const card = document.createElement("article");
    card.className = "partner-card";

    if (partner.flag) {
      const flag = document.createElement("span");
      flag.className = "flag";
      flag.textContent = partner.flag;
      card.append(flag);
    }

    const logo = document.createElement("div");
    logo.className = "partner-logo";
    const img = document.createElement("img");
    img.src = partner.logo;
    img.alt = `Логотип ${partner.name}`;
    img.width = 104;
    img.height = 104;
    img.loading = "lazy";
    if (partner.fit === "cover") img.classList.add("is-cover");
    logo.append(img);

    const name = document.createElement("h2");
    name.className = "partner-name";
    name.textContent = partner.name;

    const blurb = document.createElement("p");
    blurb.className = "partner-blurb";
    blurb.textContent = partner.blurb;

    const cta = document.createElement("button");
    cta.className = "referral";
    cta.type = "button";
    cta.textContent = partner.cta;
    cta.addEventListener("click", onStubClick);

    card.append(logo, name, blurb, cta);
    item.append(card);
    listEl.append(item);
  });
})();
