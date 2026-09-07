"""Receitas completas (ingredientes + preparo) — cozinha portuguesa e mediterrânica,
escritas de raiz (não copiadas de nenhum site). Cada receita tem uma lista de
ingredientes-chave (para cruzar com a despensa) e os macros aproximados por dose."""

RECIPES = [
    # ---------- PEQUENO-ALMOÇO / LANCHE ----------
    {
        "nome": "Omelete de ovos com espinafres e queijo fresco",
        "tags": ["pequeno_almoco", "lanche", "rapido"],
        "ingredientes": ["3 ovos", "50g de espinafres", "30g de queijo fresco", "sal e pimenta"],
        "preparo": ["Bate os ovos com sal e pimenta.", "Salteia os espinafres 1-2 min.",
                    "Junta os ovos batidos e o queijo fresco.", "Cozinha em lume brando até solidificar."],
        "kcal": 350, "proteina_g": 28, "hidratos_g": 4, "gordura_g": 24,
        "chave_despensa": ["ovos", "espinafres", "queijo fresco"],
    },
    {
        "nome": "Torradas com ovo escalfado",
        "tags": ["pequeno_almoco", "rapido"],
        "ingredientes": ["2 fatias de pão", "2 ovos", "azeite e sal"],
        "preparo": ["Leva água a ferver com um pouco de vinagre.", "Escalfa os ovos 3 min.",
                    "Torra o pão e serve com os ovos e um fio de azeite."],
        "kcal": 320, "proteina_g": 18, "hidratos_g": 30, "gordura_g": 14,
        "chave_despensa": ["pao", "ovos"],
    },
    {
        "nome": "Papas de aveia com banana e mel",
        "tags": ["pequeno_almoco", "rapido"],
        "ingredientes": ["40g de aveia", "200ml de leite", "1 banana", "1 colher de mel"],
        "preparo": ["Aquece o leite com a aveia em lume brando 5 min, mexendo.",
                    "Corta a banana e junta.", "Termina com o mel por cima."],
        "kcal": 380, "proteina_g": 14, "hidratos_g": 65, "gordura_g": 6,
        "chave_despensa": ["aveia", "leite", "banana"],
    },
    {
        "nome": "Iogurte com fruta e nozes",
        "tags": ["lanche", "pequeno_almoco", "rapido"],
        "ingredientes": ["150g de iogurte natural", "1 maçã ou banana", "20g de nozes ou amêndoas"],
        "preparo": ["Corta a fruta em pedaços.", "Junta ao iogurte e termina com as nozes por cima."],
        "kcal": 280, "proteina_g": 12, "hidratos_g": 30, "gordura_g": 12,
        "chave_despensa": ["iogurte", "maca", "banana", "nozes", "amendoas"],
    },
    {
        "nome": "Sandes de atum com pão integral",
        "tags": ["lanche", "pequeno_almoco", "rapido"],
        "ingredientes": ["1 lata de atum", "2 fatias de pão integral", "alface e tomate", "azeite"],
        "preparo": ["Escorre o atum e tempera com azeite.", "Monta a sandes com alface, tomate e atum."],
        "kcal": 350, "proteina_g": 28, "hidratos_g": 35, "gordura_g": 10,
        "chave_despensa": ["atum", "pao", "tomate", "alface"],
    },
    {
        "nome": "Panquecas de aveia e banana",
        "tags": ["pequeno_almoco"],
        "ingredientes": ["1 banana", "2 ovos", "40g de aveia", "canela a gosto"],
        "preparo": ["Tritura tudo até obter uma massa homogénea.",
                    "Cozinha em frigideira antiaderente, 2 min de cada lado.", "Serve quente."],
        "kcal": 340, "proteina_g": 18, "hidratos_g": 42, "gordura_g": 10,
        "chave_despensa": ["banana", "ovos", "aveia"],
    },
    {
        "nome": "Torrada com queijo e tomate",
        "tags": ["pequeno_almoco", "lanche", "rapido"],
        "ingredientes": ["2 fatias de pão", "30g de queijo", "1 tomate", "orégãos"],
        "preparo": ["Coloca o queijo e o tomate em cima do pão.", "Leva ao forno/torradeira até derreter.",
                    "Polvilha com orégãos."],
        "kcal": 300, "proteina_g": 14, "hidratos_g": 32, "gordura_g": 12,
        "chave_despensa": ["pao", "queijo", "tomate"],
    },
    {
        "nome": "Batido proteico com banana e aveia",
        "tags": ["lanche", "pos_treino", "rapido"],
        "ingredientes": ["1 dose de whey protein", "1 banana", "30g de aveia", "200ml de leite"],
        "preparo": ["Junta tudo no liquidificador.", "Bate até ficar homogéneo."],
        "kcal": 380, "proteina_g": 35, "hidratos_g": 45, "gordura_g": 6,
        "chave_despensa": ["whey protein", "banana", "aveia", "leite"],
    },
    {
        "nome": "Iogurte grego com aveia, banana e amendoim",
        "tags": ["pequeno_almoco", "lanche", "rapido"],
        "ingredientes": ["150g de iogurte grego", "40g de aveia", "1 banana", "1 colher de manteiga de amendoim"],
        "preparo": ["Corta a banana às rodelas.", "Junta tudo numa taça.", "Termina com a manteiga de amendoim."],
        "kcal": 480, "proteina_g": 24, "hidratos_g": 60, "gordura_g": 16,
        "chave_despensa": ["iogurte grego", "aveia", "banana", "manteiga de amendoim"],
    },
    {
        "nome": "Ovos mexidos com pão e queijo fresco",
        "tags": ["pequeno_almoco", "rapido"],
        "ingredientes": ["3 ovos", "2 fatias de pão", "30g de queijo fresco", "sal e pimenta"],
        "preparo": ["Mexe os ovos em lume brando com sal e pimenta.",
                    "Junta o queijo fresco no final.", "Serve com o pão torrado."],
        "kcal": 400, "proteina_g": 26, "hidratos_g": 30, "gordura_g": 18,
        "chave_despensa": ["ovos", "pao", "queijo fresco"],
    },

    # ---------- SOPAS ----------
    {
        "nome": "Caldo verde",
        "tags": ["jantar", "leve"],
        "ingredientes": ["2 batatas", "couve picada", "1 cebola", "azeite"],
        "preparo": ["Coze as batatas e a cebola até desfazer.", "Tritura até ficar cremoso.",
                    "Junta a couve cortada finamente e coze mais 5 min.", "Tempera com azeite."],
        "kcal": 280, "proteina_g": 6, "hidratos_g": 50, "gordura_g": 6,
        "chave_despensa": ["batata", "couve", "cebola"],
    },
    {
        "nome": "Sopa de legumes com feijão",
        "tags": ["jantar", "leve"],
        "ingredientes": ["cenoura, batata e courgette", "150g de feijão cozido", "1 cebola", "azeite"],
        "preparo": ["Refoga a cebola em azeite.", "Junta os legumes e água, coze 20 min.",
                    "Junta o feijão no final e aquece mais 5 min."],
        "kcal": 300, "proteina_g": 14, "hidratos_g": 45, "gordura_g": 6,
        "chave_despensa": ["cenoura", "batata", "feijao", "cebola"],
    },
    {
        "nome": "Canja de galinha",
        "tags": ["jantar", "leve"],
        "ingredientes": ["150g de frango desfiado", "50g de arroz ou massa miúda", "1 cenoura", "1 cebola"],
        "preparo": ["Coze o frango com a cebola e a cenoura em água até ficar tenro.",
                    "Retira o frango, desfia e volta a juntar.", "Junta o arroz e deixa cozer mais 15 min."],
        "kcal": 320, "proteina_g": 30, "hidratos_g": 30, "gordura_g": 6,
        "chave_despensa": ["frango", "arroz", "cenoura", "cebola"],
    },
    {
        "nome": "Creme de cenoura",
        "tags": ["jantar", "leve"],
        "ingredientes": ["4 cenouras", "1 batata", "1 cebola", "azeite"],
        "preparo": ["Refoga a cebola em azeite.", "Junta a cenoura e a batata cortadas e água.",
                    "Coze 20 min e tritura até ficar cremoso."],
        "kcal": 220, "proteina_g": 4, "hidratos_g": 40, "gordura_g": 6,
        "chave_despensa": ["cenoura", "batata", "cebola"],
    },
    {
        "nome": "Sopa de grão com espinafres",
        "tags": ["jantar", "leve"],
        "ingredientes": ["150g de grão cozido", "punhado de espinafres", "1 cebola", "azeite e alho"],
        "preparo": ["Refoga a cebola e o alho em azeite.", "Junta o grão e água, deixa apurar 10 min.",
                    "Junta os espinafres no final até murcharem."],
        "kcal": 280, "proteina_g": 14, "hidratos_g": 40, "gordura_g": 8,
        "chave_despensa": ["grao", "espinafres", "cebola"],
    },
    {
        "nome": "Sopa de tomate com ovo escalfado",
        "tags": ["jantar", "leve"],
        "ingredientes": ["4 tomates maduros", "1 cebola", "1-2 ovos", "azeite e alho"],
        "preparo": ["Refoga a cebola e o alho em azeite.", "Junta o tomate picado e um pouco de água, deixa apurar.",
                    "Escalfa o ovo diretamente na sopa nos últimos minutos."],
        "kcal": 260, "proteina_g": 12, "hidratos_g": 20, "gordura_g": 14,
        "chave_despensa": ["tomate", "cebola", "ovos"],
    },

    # ---------- CARNE ----------
    {
        "nome": "Frango grelhado com arroz e brócolos",
        "tags": ["almoco", "jantar", "proteico"],
        "ingredientes": ["150g de peito de frango", "80g de arroz (cru)", "150g de brócolos", "azeite"],
        "preparo": ["Tempera o frango e grelha 5-6 min de cada lado.", "Coze o arroz 15 min.",
                    "Coze os brócolos no vapor.", "Serve tudo com um fio de azeite."],
        "kcal": 520, "proteina_g": 48, "hidratos_g": 55, "gordura_g": 12,
        "chave_despensa": ["frango", "arroz", "brocolos"],
    },
    {
        "nome": "Arroz de frango simples",
        "tags": ["almoco", "jantar"],
        "ingredientes": ["150g de frango em pedaços", "80g de arroz (cru)", "1 tomate", "1 cebola"],
        "preparo": ["Refoga a cebola e alho.", "Junta o frango e deixa alourar.",
                    "Adiciona o tomate e o arroz, mexe bem.", "Junta água e coze até o arroz ficar macio."],
        "kcal": 540, "proteina_g": 40, "hidratos_g": 60, "gordura_g": 14,
        "chave_despensa": ["frango", "arroz", "tomate", "cebola"],
    },
    {
        "nome": "Frango estufado com legumes",
        "tags": ["almoco", "jantar"],
        "ingredientes": ["150g de frango em pedaços", "cenoura e batata", "1 cebola", "tomate"],
        "preparo": ["Refoga a cebola em azeite.", "Junta o frango e deixa alourar.",
                    "Adiciona o tomate, cenoura e batata.", "Tapa e deixa cozinhar 25-30 min."],
        "kcal": 460, "proteina_g": 38, "hidratos_g": 30, "gordura_g": 16,
        "chave_despensa": ["frango", "cenoura", "batata", "cebola", "tomate"],
    },
    {
        "nome": "Bifanas com pão",
        "tags": ["almoco", "jantar"],
        "ingredientes": ["150g de bifanas de porco", "1 pão", "alho e louro", "mostarda a gosto"],
        "preparo": ["Marina a carne com alho e louro.", "Grelha ou frita em pouco azeite.",
                    "Serve dentro do pão com um pouco do molho e mostarda."],
        "kcal": 480, "proteina_g": 35, "hidratos_g": 40, "gordura_g": 18,
        "chave_despensa": ["porco", "pao"],
    },
    {
        "nome": "Carne de porco à moda alentejana simplificada",
        "tags": ["almoco", "jantar"],
        "ingredientes": ["150g de carne de porco em cubos", "150g de amêijoas ou camarão", "1 batata", "alho e colorau"],
        "preparo": ["Marina a carne com alho e colorau.", "Frita a carne até dourar.",
                    "Junta as amêijoas/camarão e deixa cozinhar mais 5 min.", "Serve com batata frita ou cozida."],
        "kcal": 520, "proteina_g": 42, "hidratos_g": 30, "gordura_g": 22,
        "chave_despensa": ["porco", "camarao", "batata"],
    },
    {
        "nome": "Febras grelhadas com batata",
        "tags": ["almoco", "jantar"],
        "ingredientes": ["150g de febras de porco", "2 batatas", "alho e louro"],
        "preparo": ["Tempera as febras com alho e louro.", "Grelha 4-5 min de cada lado.",
                    "Serve com batata cozida ou assada."],
        "kcal": 450, "proteina_g": 38, "hidratos_g": 35, "gordura_g": 14,
        "chave_despensa": ["porco", "batata"],
    },
    {
        "nome": "Frango assado com batata a murro",
        "tags": ["almoco", "jantar"],
        "ingredientes": ["200g de frango (coxa ou peito)", "3 batatas pequenas", "alho e alecrim", "azeite"],
        "preparo": ["Tempera o frango com alho e alecrim.", "Assa no forno 35-40 min com as batatas.",
                    "No fim, esmaga levemente as batatas e regue com azeite."],
        "kcal": 550, "proteina_g": 42, "hidratos_g": 45, "gordura_g": 18,
        "chave_despensa": ["frango", "batata"],
    },
    {
        "nome": "Almôndegas de carne com massa",
        "tags": ["almoco", "jantar"],
        "ingredientes": ["200g de carne picada", "80g de massa (crua)", "molho de tomate", "1 ovo"],
        "preparo": ["Mistura a carne picada com o ovo e tempera.", "Molda em bolinhas e frita ou assa.",
                    "Junta ao molho de tomate e deixa apurar.", "Serve com a massa cozida."],
        "kcal": 560, "proteina_g": 38, "hidratos_g": 55, "gordura_g": 18,
        "chave_despensa": ["carne", "massa", "tomate", "ovos"],
    },
    {
        "nome": "Costeletas de porco grelhadas com arroz",
        "tags": ["almoco", "jantar"],
        "ingredientes": ["2 costeletas de porco", "80g de arroz (cru)", "alho e louro"],
        "preparo": ["Tempera as costeletas com alho e louro.", "Grelha 4-5 min de cada lado.",
                    "Serve com arroz branco."],
        "kcal": 520, "proteina_g": 40, "hidratos_g": 45, "gordura_g": 20,
        "chave_despensa": ["porco", "arroz"],
    },
    {
        "nome": "Peru estufado com legumes",
        "tags": ["almoco", "jantar"],
        "ingredientes": ["150g de peru em pedaços", "cenoura e courgette", "1 cebola", "tomate"],
        "preparo": ["Refoga a cebola em azeite.", "Junta o peru e deixa alourar.",
                    "Adiciona os legumes e o tomate.", "Tapa e cozinha 20-25 min."],
        "kcal": 400, "proteina_g": 40, "hidratos_g": 20, "gordura_g": 12,
        "chave_despensa": ["peru", "cenoura", "cebola", "tomate"],
    },
    {
        "nome": "Salada de frango com queijo e nozes",
        "tags": ["almoco", "jantar", "leve"],
        "ingredientes": ["150g de peito de frango", "alface e tomate", "30g de queijo", "20g de nozes"],
        "preparo": ["Grelha o frango e corta em tiras.", "Monta a base de alface e tomate.",
                    "Junta o frango, queijo e nozes.", "Tempera com azeite e limão."],
        "kcal": 450, "proteina_g": 42, "hidratos_g": 12, "gordura_g": 26,
        "chave_despensa": ["frango", "alface", "tomate", "queijo", "nozes"],
    },
    {
        "nome": "Rojões simplificados",
        "tags": ["almoco", "jantar"],
        "ingredientes": ["150g de carne de porco em cubos", "2 batatas", "alho, louro e colorau"],
        "preparo": ["Marina a carne com alho, louro e colorau.", "Frita em lume médio até dourar bem.",
                    "Serve com batata cozida ou frita."],
        "kcal": 500, "proteina_g": 36, "hidratos_g": 35, "gordura_g": 22,
        "chave_despensa": ["porco", "batata"],
    },

    # ---------- PEIXE / MARISCO ----------
    {
        "nome": "Bacalhau com batata e cebolada",
        "tags": ["almoco", "jantar"],
        "ingredientes": ["1 posta de bacalhau demolhado", "2 batatas", "1 cebola", "louro"],
        "preparo": ["Coze o bacalhau e as batatas com louro 15-20 min.",
                    "Corta a cebola às rodelas e refoga até dourar.", "Serve com a cebolada por cima."],
        "kcal": 480, "proteina_g": 38, "hidratos_g": 40, "gordura_g": 16,
        "chave_despensa": ["bacalhau", "batata", "cebola"],
    },
    {
        "nome": "Bacalhau à Brás",
        "tags": ["almoco", "jantar"],
        "ingredientes": ["150g de bacalhau desfiado", "2 batatas (palha)", "3 ovos", "1 cebola"],
        "preparo": ["Refoga a cebola e junta o bacalhau desfiado.", "Junta a batata palha.",
                    "Adiciona os ovos batidos e mexe em lume brando até cremoso."],
        "kcal": 520, "proteina_g": 34, "hidratos_g": 40, "gordura_g": 24,
        "chave_despensa": ["bacalhau", "batata", "ovos", "cebola"],
    },
    {
        "nome": "Bacalhau com natas simplificado",
        "tags": ["almoco", "jantar"],
        "ingredientes": ["150g de bacalhau desfiado", "2 batatas (palha)", "200ml de natas", "1 cebola"],
        "preparo": ["Refoga a cebola com o bacalhau.", "Junta a batata palha e as natas.",
                    "Mistura tudo e leva ao forno até dourar."],
        "kcal": 560, "proteina_g": 30, "hidratos_g": 35, "gordura_g": 32,
        "chave_despensa": ["bacalhau", "batata", "cebola"],
    },
    {
        "nome": "Filetes de pescada com arroz",
        "tags": ["almoco", "jantar", "leve"],
        "ingredientes": ["150g de filetes de pescada", "80g de arroz (cru)", "farinha e ovo para panar", "azeite"],
        "preparo": ["Passa os filetes por farinha e ovo.", "Frita em pouco azeite até dourar.",
                    "Serve com arroz branco."],
        "kcal": 450, "proteina_g": 32, "hidratos_g": 50, "gordura_g": 14,
        "chave_despensa": ["pescada", "arroz", "ovos"],
    },
    {
        "nome": "Peixe grelhado com legumes salteados",
        "tags": ["almoco", "jantar", "leve"],
        "ingredientes": ["150g de peixe (pescada ou salmão)", "legumes a gosto", "azeite e limão"],
        "preparo": ["Tempera o peixe com sal e limão.", "Grelha 3-4 min de cada lado.",
                    "Salteia os legumes em azeite e serve junto."],
        "kcal": 380, "proteina_g": 35, "hidratos_g": 12, "gordura_g": 18,
        "chave_despensa": ["peixe", "salmao", "pescada", "legumes"],
    },
    {
        "nome": "Arroz de marisco simplificado",
        "tags": ["almoco", "jantar"],
        "ingredientes": ["150g de camarão ou mistura de marisco", "80g de arroz (cru)", "1 tomate", "alho e colorau"],
        "preparo": ["Refoga o alho e o tomate em azeite com colorau.", "Junta o arroz e água, deixa cozer.",
                    "Nos últimos minutos, junta o marisco até cozinhar."],
        "kcal": 480, "proteina_g": 30, "hidratos_g": 60, "gordura_g": 10,
        "chave_despensa": ["camarao", "marisco", "arroz", "tomate"],
    },
    {
        "nome": "Sardinhas assadas com batata e pimentos",
        "tags": ["almoco", "jantar"],
        "ingredientes": ["4 sardinhas frescas", "2 batatas", "pimentos a gosto", "azeite"],
        "preparo": ["Tempera as sardinhas com sal grosso.", "Assa ou grelha na brasa/forno.",
                    "Serve com batata cozida e pimentos assados."],
        "kcal": 420, "proteina_g": 32, "hidratos_g": 30, "gordura_g": 20,
        "chave_despensa": ["sardinhas", "batata"],
    },
    {
        "nome": "Polvo com batata a murro (versão simples)",
        "tags": ["almoco", "jantar"],
        "ingredientes": ["200g de polvo cozido", "3 batatas pequenas", "azeite e alho"],
        "preparo": ["Coze as batatas e esmaga levemente.", "Aquece o polvo em azeite com alho.",
                    "Serve tudo regado com azeite."],
        "kcal": 460, "proteina_g": 38, "hidratos_g": 35, "gordura_g": 18,
        "chave_despensa": ["polvo", "batata"],
    },
    {
        "nome": "Massa com atum e tomate",
        "tags": ["almoco", "jantar"],
        "ingredientes": ["80g de massa (crua)", "1 lata de atum", "molho de tomate", "orégãos"],
        "preparo": ["Coze a massa.", "Aquece o molho de tomate com azeite.",
                    "Junta o atum escorrido e os orégãos.", "Mistura com a massa."],
        "kcal": 500, "proteina_g": 32, "hidratos_g": 65, "gordura_g": 10,
        "chave_despensa": ["massa", "atum", "tomate"],
    },
    {
        "nome": "Salmão grelhado com legumes",
        "tags": ["almoco", "jantar", "leve"],
        "ingredientes": ["150g de salmão", "brócolos e cenoura", "azeite e limão"],
        "preparo": ["Tempera o salmão com sal e limão.", "Grelha 4 min de cada lado.",
                    "Salteia os legumes em azeite e serve junto."],
        "kcal": 420, "proteina_g": 34, "hidratos_g": 12, "gordura_g": 26,
        "chave_despensa": ["salmao", "brocolos", "cenoura"],
    },
    {
        "nome": "Camarão salteado com alho e arroz",
        "tags": ["almoco", "jantar"],
        "ingredientes": ["150g de camarão", "80g de arroz (cru)", "alho e azeite", "salsa a gosto"],
        "preparo": ["Salteia o camarão em azeite com alho até rosado.",
                    "Serve com arroz branco e salsa picada por cima."],
        "kcal": 400, "proteina_g": 32, "hidratos_g": 45, "gordura_g": 10,
        "chave_despensa": ["camarao", "arroz"],
    },

    # ---------- VEGETARIANAS / LEGUMINOSAS ----------
    {
        "nome": "Feijoada de legumes com ovo",
        "tags": ["almoco", "jantar"],
        "ingredientes": ["150g de feijão cozido", "cenoura e cebola", "1-2 ovos", "azeite, alho e louro"],
        "preparo": ["Refoga a cebola e o alho.", "Junta os legumes e deixa amolecer.",
                    "Adiciona o feijão e água, deixa apurar.", "Escalfa/frita o ovo e serve por cima."],
        "kcal": 400, "proteina_g": 22, "hidratos_g": 45, "gordura_g": 12,
        "chave_despensa": ["feijao", "cenoura", "cebola", "ovos"],
    },
    {
        "nome": "Salada mediterrânica de grão",
        "tags": ["almoco", "leve"],
        "ingredientes": ["150g de grão cozido", "tomate e pepino", "azeitonas", "queijo feta (opcional)"],
        "preparo": ["Junta o grão com o tomate e pepino picados.", "Adiciona as azeitonas e o queijo.",
                    "Tempera com azeite, limão e orégãos."],
        "kcal": 380, "proteina_g": 16, "hidratos_g": 45, "gordura_g": 14,
        "chave_despensa": ["grao", "tomate", "queijo"],
    },
    {
        "nome": "Tortilha de batata e ovo",
        "tags": ["almoco", "jantar", "pequeno_almoco"],
        "ingredientes": ["3 ovos", "2 batatas", "1 cebola", "azeite"],
        "preparo": ["Frita a batata e a cebola em fatias finas até macias.", "Bate os ovos e tempera.",
                    "Junta tudo e cozinha numa frigideira dos dois lados."],
        "kcal": 430, "proteina_g": 20, "hidratos_g": 35, "gordura_g": 22,
        "chave_despensa": ["ovos", "batata", "cebola"],
    },
    {
        "nome": "Empadão de batata vegetariano",
        "tags": ["almoco", "jantar"],
        "ingredientes": ["3 batatas", "150g de legumes picados", "1 ovo", "queijo ralado"],
        "preparo": ["Coze e esmaga as batatas em puré.", "Salteia os legumes e coloca numa base.",
                    "Cobre com o puré e queijo.", "Leva ao forno até dourar."],
        "kcal": 420, "proteina_g": 16, "hidratos_g": 55, "gordura_g": 14,
        "chave_despensa": ["batata", "legumes", "queijo", "ovos"],
    },
    {
        "nome": "Migas de couve simplificadas",
        "tags": ["jantar"],
        "ingredientes": ["pão duro", "couve picada", "alho e azeite", "1 ovo (opcional)"],
        "preparo": ["Refoga o alho em azeite.", "Junta a couve e deixa murchar.",
                    "Junta o pão desfeito e um pouco de água, mexe até formar uma pasta.",
                    "Serve com ovo frito por cima, se quiseres."],
        "kcal": 350, "proteina_g": 10, "hidratos_g": 50, "gordura_g": 12,
        "chave_despensa": ["pao", "couve"],
    },
    {
        "nome": "Açorda de alho simplificada",
        "tags": ["jantar", "leve"],
        "ingredientes": ["pão duro", "alho e coentros", "1-2 ovos", "azeite"],
        "preparo": ["Refoga o alho em azeite.", "Junta água e leva a ferver.",
                    "Junta o pão desfeito e mexe até engrossar.", "Escalfa o ovo diretamente e serve com coentros."],
        "kcal": 320, "proteina_g": 14, "hidratos_g": 45, "gordura_g": 10,
        "chave_despensa": ["pao", "ovos"],
    },
    {
        "nome": "Grão salteado com espinafres",
        "tags": ["almoco", "jantar", "leve"],
        "ingredientes": ["150g de grão cozido", "punhado de espinafres", "alho e azeite", "colorau"],
        "preparo": ["Refoga o alho em azeite com colorau.", "Junta o grão e deixa alourar levemente.",
                    "Adiciona os espinafres até murcharem."],
        "kcal": 320, "proteina_g": 15, "hidratos_g": 40, "gordura_g": 10,
        "chave_despensa": ["grao", "espinafres"],
    },
    {
        "nome": "Lentilhas estufadas com legumes",
        "tags": ["almoco", "jantar"],
        "ingredientes": ["150g de lentilhas cozidas", "cenoura e cebola", "tomate", "azeite e louro"],
        "preparo": ["Refoga a cebola e a cenoura em azeite.", "Junta o tomate picado e o louro.",
                    "Adiciona as lentilhas e um pouco de água, deixa apurar 10 min."],
        "kcal": 340, "proteina_g": 18, "hidratos_g": 50, "gordura_g": 8,
        "chave_despensa": ["lentilhas", "cenoura", "cebola", "tomate"],
    },
    {
        "nome": "Arroz de tomate simples",
        "tags": ["almoco", "jantar", "leve"],
        "ingredientes": ["80g de arroz (cru)", "3 tomates maduros", "1 cebola", "azeite e alho"],
        "preparo": ["Refoga a cebola e o alho em azeite.", "Junta o tomate picado e deixa apurar.",
                    "Adiciona o arroz e água, deixa cozer até macio."],
        "kcal": 380, "proteina_g": 8, "hidratos_g": 70, "gordura_g": 8,
        "chave_despensa": ["arroz", "tomate", "cebola"],
    },
    {
        "nome": "Batata doce assada com ovo e espinafres",
        "tags": ["almoco", "jantar", "leve"],
        "ingredientes": ["1 batata doce grande", "punhado de espinafres", "1-2 ovos", "azeite"],
        "preparo": ["Assa a batata doce até macia (forno ou microondas).", "Salteia os espinafres em azeite.",
                    "Frita ou escalfa o ovo.", "Serve tudo junto."],
        "kcal": 360, "proteina_g": 16, "hidratos_g": 45, "gordura_g": 12,
        "chave_despensa": ["batata doce", "espinafres", "ovos"],
    },

    # ---------- PRATOS TRADICIONAIS (versões simplificadas) ----------
    {
        "nome": "Cozido à portuguesa simplificado",
        "tags": ["almoco", "jantar"],
        "ingredientes": ["150g de carne de porco ou vaca", "chouriço", "batata, cenoura e couve", "grão cozido"],
        "preparo": ["Coze a carne e o chouriço em água durante 40 min.",
                    "Junta a batata, cenoura e couve e deixa cozer mais 20 min.",
                    "Junta o grão no final e serve tudo junto."],
        "kcal": 620, "proteina_g": 42, "hidratos_g": 45, "gordura_g": 28,
        "chave_despensa": ["porco", "chourico", "batata", "cenoura", "couve", "grao"],
    },
    {
        "nome": "Francesinha leve (versão simplificada)",
        "tags": ["almoco", "jantar"],
        "ingredientes": ["2 fatias de pão", "fatia de carne (bife ou fiambre)", "queijo", "molho de tomate"],
        "preparo": ["Monta a sandes com a carne e o fiambre entre o pão.", "Cobre com queijo.",
                    "Leva ao forno até derreter e regue com o molho de tomate."],
        "kcal": 560, "proteina_g": 34, "hidratos_g": 45, "gordura_g": 26,
        "chave_despensa": ["pao", "queijo", "carne", "tomate"],
    },
    {
        "nome": "Chanfana simplificada (guisado de carne)",
        "tags": ["almoco", "jantar"],
        "ingredientes": ["200g de carne de porco ou cabrito", "cebola e alho", "vinho tinto (opcional)", "louro"],
        "preparo": ["Marina a carne com alho, louro e vinho (se usares).",
                    "Refoga a cebola e junta a carne, deixa alourar.",
                    "Tapa e deixa cozinhar em lume brando 1h, até a carne ficar macia."],
        "kcal": 480, "proteina_g": 38, "hidratos_g": 8, "gordura_g": 28,
        "chave_despensa": ["porco", "cebola"],
    },
    {
        "nome": "Arroz de pato simplificado",
        "tags": ["almoco", "jantar"],
        "ingredientes": ["150g de pato ou frango desfiado", "80g de arroz (cru)", "chouriço", "cebola"],
        "preparo": ["Coze o pato/frango com a cebola até tenro, desfia.",
                    "Refoga o chouriço fatiado.", "Junta o arroz ao caldo da cozedura e deixa cozer.",
                    "Junta a carne desfiada e serve."],
        "kcal": 560, "proteina_g": 35, "hidratos_g": 60, "gordura_g": 18,
        "chave_despensa": ["frango", "arroz", "chourico", "cebola"],
    },
    {
        "nome": "Caldeirada de peixe simplificada",
        "tags": ["almoco", "jantar"],
        "ingredientes": ["200g de peixe variado", "batata", "tomate e cebola", "azeite e louro"],
        "preparo": ["Faz camadas de cebola, tomate e batata numa panela.",
                    "Coloca o peixe por cima.", "Rega com azeite e um pouco de água.",
                    "Deixa cozinhar em lume brando 25-30 min sem mexer muito."],
        "kcal": 420, "proteina_g": 32, "hidratos_g": 35, "gordura_g": 14,
        "chave_despensa": ["peixe", "batata", "tomate", "cebola"],
    },
]


def sugerir_receitas(pantry_nomes, restante_kcal, restante_prot, excluidos_nomes=None, top_n=6, receitas_extra=None):
    """Classifica as receitas em duas categorias:
    - 'prontas': tens TODOS os ingredientes-chave em casa.
    - 'quase': falta-te exatamente 1 ingrediente-chave.
    Todas as outras (falta 2+) não aparecem — só sugerimos o que faz sentido já ou quase.
    Receitas com um alimento excluído são descartadas por completo.
    receitas_extra: receitas criadas pelo próprio utilizador (mesmo formato), incluídas na mistura."""
    pantry_lower = [p.lower() for p in pantry_nomes]
    excluidos_lower = [e.lower() for e in (excluidos_nomes or [])]

    prontas, quase = [], []
    for r in RECIPES + list(receitas_extra or []):
        chaves = [c.lower() for c in r["chave_despensa"]]

        tem_excluido = any(
            any(exc in chave or chave in exc for chave in chaves)
            for exc in excluidos_lower
        )
        if tem_excluido:
            continue

        tem = [chave for chave in chaves if any(chave in p or p in chave for p in pantry_lower)]
        falta = [chave for chave in chaves if chave not in tem]
        match_count = len(tem)
        total_chaves = len(r["chave_despensa"])

        cabe_kcal = r["kcal"] <= max(restante_kcal, 1) * 1.3
        ajuda_proteina = r["proteina_g"] >= (restante_prot * 0.25 if restante_prot > 0 else 0)
        score = (1 if cabe_kcal else 0) + (1 if ajuda_proteina else 0)

        item = {"receita": r, "match_count": match_count, "faltam": falta, "_score": score}
        if len(falta) == 0:
            prontas.append(item)
        elif len(falta) == 1:
            quase.append(item)

    prontas.sort(key=lambda x: -x["_score"])
    quase.sort(key=lambda x: -x["_score"])
    return prontas[:top_n], quase[:top_n]
