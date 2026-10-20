# Validation report

Full automated validation passed. This means preservation against the available backup, not confirmation that the original website or backup contained every historical record.

## Source and coverage

| Post type | Source | Export |
| --- | ---: | ---: |
| attachment | 678 | 678 |
| custom_css | 2 | 2 |
| nav_menu_item | 5 | 5 |
| oembed_cache | 74 | 74 |
| page | 16 | 16 |
| post | 49,710 | 49,710 |
| revision | 1 | 1 |
| seopress_404 | 12 | 12 |
| seopress_schemas | 2 | 2 |
| wpcf7_contact_form | 1 | 1 |
| wpforms | 1 | 1 |

Total: **50,502** unique source IDs and exported records. Content folders: **49,818**. Navigation (5), attachments (678) and revisions (1) are separately classified.

### Counts by type and status

| Type | Status | Count |
| --- | --- | ---: |
| attachment | inherit | 678 |
| custom_css | publish | 2 |
| nav_menu_item | publish | 5 |
| oembed_cache | publish | 74 |
| page | publish | 16 |
| post | auto-draft | 1 |
| post | publish | 49,709 |
| revision | inherit | 1 |
| seopress_404 | publish | 12 |
| seopress_schemas | draft | 1 |
| seopress_schemas | publish | 1 |
| wpcf7_contact_form | publish | 1 |
| wpforms | publish | 1 |

No source pending, private, future/scheduled or trash records were found. No statuses were converted or omitted.

## Complete title/body and structure checks

- All **50,502** source rows were re-read from SQL with an independent regex tokenizer/escape decoder; decoded title and body hashes match exported JSONL exactly. **Zero mismatches.**
- All **49,818** eligible content.html files match the full source body bytes; all matching metadata files equal their JSONL record fields.
- Source/export ID sets, unique IDs, type/status pairs, every original public post-table field, **170,362** retained postmeta rows, taxonomy relationship IDs/order and CSV full titles passed record-by-record checks.
- Every JSON and JSONL file parses. Duplicate IDs and overwritten ID paths were checked. Duplicate titles/slugs were preserved, not merged.
- Duplicate-title groups: 388; duplicate-slug groups: 45. IDs are in duplicate-groups.jsonl.
- SQL, inner archive and original ZIP hashes were rechecked unchanged. ZIP CRC and inner archive lengths/paths were checked. Source hashes are in manifest.json.

### Encoding and content features

| Feature present in source title/body | Records |
| --- | ---: |
| HTML | 49,730 |
| shortcodes | 2,740 |
| Cyrillic | 9 |
| replacement_character | 2 |

All title/body characters, including the listed scripts, emoji, HTML, block comments and shortcodes, were covered by the full hashes. A feature absent from this table was not observed. Existing U+FFFD replacement characters, if listed, originate in source content and are preserved rather than guessed/repaired.

### Flags

```json
{
  "empty_body": 691,
  "empty_body_attachment": 675,
  "empty_body_custom_css": 1,
  "unusually_large_body": 25,
  "empty_body_post": 1,
  "empty_title": 79,
  "empty_body_seopress_404": 12,
  "empty_body_seopress_schemas": 2
}
```
Largest body: ID 57574, 161,116 UTF-8 bytes. Empty values and large bodies are flagged and preserved; nothing was filled in.

## Media

```json
{
  "upload_files": 9715,
  "preserved_files": 8532,
  "preserved_bytes": 208460493,
  "excluded_support_files": 1183,
  "attachment_records_with_available_files": 629,
  "attachment_records_without_available_files": 49,
  "attachment_records_without_resolvable_path": 0,
  "body_upload_references": 532,
  "body_upload_references_missing": 517,
  "external_embed_references": 1702,
  "unresolved_relative_embed_references": 265,
  "unique_body_upload_paths": 529,
  "unique_body_upload_paths_missing": 514
}
```
All **8,532** copied files were rehashed against archive-entry hashes. Every claimed local media path exists. Unresolved attachment-ID references: **128** (reference-issues.jsonl).

Some missing attachment references have differently named archive candidates (for example, a database filename begins `Óleo-de-colza` while the archive filename begins `leo-de-colza`). These are not automatically treated as verified matches. All actual image files are preserved. Missing-reference counts are reference occurrences, not necessarily distinct files. External URLs and unresolved relative URLs are recorded without downloading or claiming availability. Dynamic shortcode execution, URLs generated at runtime and remote availability were not verified. Original bodies retain references that a static scanner cannot interpret.

## Redactions and boundaries

Credential/password fields excluded: **1**. Field paths/reasons are in redactions.json. The original backup remains unchanged. Private account/customer data and raw SQL were not included.

Existing root README was preserved. No WordPress code/plugins were executed and no content was published. Media is preserved as data. No live-site completeness, external-link availability, historical pre-backup encoding or executable shortcode behavior is asserted.

## Readable representative spot-checks

These excerpts supplement the complete automated comparisons; they do not replace them. Titles and body openings/endings were inspected as text, without executing HTML.

### ID 21 (custom_css)

oceanwp

Body size: 632 UTF-8 bytes.

```text
/** Center Align Meta and Content **/
ul.meta li {
    float: none;
    display: inline-block;
}
.single-post .site-content{
	text-align: center;
}
.entry-content{
	text-align: justify;
}

/** Color **/
#footer .oceanwp-about-me .oceanwp-about-me-name {
    color: #fff;
}


/** WP Contact Form **/
body div.wpforms-container-full .wpforms-form input.wpforms-field-medium, body div.wpforms-container-full .wpforms-form input.wpforms-field-medium, body div.wpforms-container-full .wpforms-form select.wpforms-field-medium, body div.wpforms-container-full .wpforms-form .wpforms-field-row.wpforms-field-medium {
    max-width: 100%;
}
... [excerpt only; full body remains in export] ...
wpforms-form input.wpforms-field-medium, body div.wpforms-container-full .wpforms-form input.wpforms-field-medium, body div.wpforms-container-full .wpforms-form select.wpforms-field-medium, body div.wpforms-container-full .wpforms-form .wpforms-field-row.wpforms-field-medium {
    max-width: 100%;
}
```

### ID 101 (page)

Contato

Body size: 2,103 UTF-8 bytes.

```text
<h2>Entre em contato com a Saudeteu.info</h2>
Nós adoraríamos ouvir de você! Use os endereços de e-mail abaixo para nos informar sobre o que você está pensando ou para nos fazer uma pergunta.
<h3><strong>Geral pergunta</strong></h3>
Está com problemas para acessar as páginas do SaudeTeu.info? Tem alguma dúvida sobre algum dos nossos artigos? Um problema com um produto? Envie-nos um email para: <span data-sheets-value="{&quot;1&quot;:2,&quot;2&quot;:&quot;Dr.Ambber1@gmail.com&quot;}" data-sheets-userformat="{&quot;2&quot;:513,&quot;3&quot;:{&quot;1&quot;:0},&quot;12&quot;:0}">Dr.Ambber1@gmail.com</span>
<h3><strong>Publicidade / Vendas</strong></h3>
Estamos ansiosos para conversar com vo
... [excerpt only; full body remains in export] ...
rá a melhorar.

Tenha em atenção que, embora possamos não conseguir responder diretamente a todos os comentários, incorporamo-lo no nosso conteúdo sempre que possível.

<span class="goog-text-highlight">Obrigado por visitar a Saude Teu</span>

[contact-form-7 id="16080" title="Contact form 1"]
```

### ID 175 (post)

15 benefícios de saúde impressionantes do óleo de cravo

Body size: 9,974 UTF-8 bytes.

```text
<span class="">Os benefícios de saúde incluem tratamento de infecções, combate à inflamação da garganta e da boca, tratamento da dor de dente, aumento do sistema imunológico, minimização do estresse, tratamento de problemas respiratórios, alívio do efeito de vômitos e náuseas, combate à fadiga, tratamento de acne, faíscas ejaculação precoce e tratamento de Sty.</span>
<div id="natur-939280281" class="natur-gig"></div>
<h2>O que é o óleo de cravo?</h2>
Indigenous to Madagascar and Indonesia, clove oil from cloves are found in nature as the pink flower buds of the evergreen tree. They are hand-picked, and the buds are left to dry until they turn brown, and after grinding them, the powder is
... [excerpt only; full body remains in export] ...
saudeteu.info/11-benefits-lentils/">11 Benefícios para a saúde surpreendentes das lentilhas </a>
<a href="https://saudeteu.info/13-beneficios-limao/">13 Benefícios para a saúde impressionantes dos limões</a>

</div>
<div class="post_author_plugin">
<div class="post_author_avatar"></div>
</div>
```

### ID 178 (post)

12 maravilhosos benefícios da viagem

Body size: 9,404 UTF-8 bytes.

```text
<span class="goog-text-highlight">Se viajar pelo mundo estiver na sua lista de desejos há algum tempo, mas você não consegue justificar o custo de fazê-lo, então você está com sorte. </span>Simplificando, viajar tem inúmeros benefícios que você pode aproveitar, independentemente do seu estado financeiro atual.
<div id="natur-292675561" class="natur-gig"></div>
Viajar é um agente terapêutico maravilhoso que pode melhorar sua saúde também, especialmente se você o tempo quando você mais precisa. Quer saber quais são alguns dos benefícios que você provavelmente experimentará? Então continue a ler para descobrir abaixo!
<h2><strong>9 benefícios maravilhosos de viajar</strong></h2>
<h3><strong
... [excerpt only; full body remains in export] ...
 </span></a>
<a href="https://saudeteu.info/13-beneficios-de-sementes-de-cominho/"><span class="">13 Benefícios da massagem nos pés e reflexologia </span></a>
<a href="https://saudeteu.info/13-remedios-caseiros-mau-halito/"><span class="">13 Remédios caseiros para o mau hálito</span></a>

</div>
```

### ID 181 (post)

11 benefícios de se manter longe das mídias sociais

Body size: 9,559 UTF-8 bytes.

```text
<span class="">Os benefícios de ficar longe das mídias sociais incluem recuperar sua privacidade, aumentar a produtividade, melhorar sua confiança, melhorar seu humor, reacender a amizade, melhorar o sono, apreciar o ambiente, melhorar sua postura, tornar-se mais atento, aumentar a criatividade e superar o medo perdendo.</span>
<div id="natur-1705175642" class="natur-gig"></div>
<span class="">Parece que há uma plataforma de mídia social em todos os lugares que você liga hoje.</span>É quase como uma droga viciante com mais de 1 bilhão de consumidores regulares. E se você olhar para os números absolutos, é realmente pior em muitos aspectos. Em média, um usuário de mídia social gasta cerca d
... [excerpt only; full body remains in export] ...
s-unicos/">8 Benefícios surpreendentes de ser único </a>
<a href="https://saudeteu.info/13-beneficios-de-sementes-de-cominho/">13 Benefícios da massagem nos pés e reflexologia </a>
<a href="https://saudeteu.info/13-remedios-caseiros-mau-halito/">13 Remédios caseiros para o mau hálito</a>

</div>
```

### ID 3324 (post)

10 Benefícios comprovados do vinagre de maçã

Body size: 8,079 UTF-8 bytes.

```text
Os benefícios de saúde incluem a promoção da perda de peso, ajuda a combater diabetes, ajuda a combater doenças cardíacas, ajuda a controlar a pressão arterial e nível de colesterol, pode ajudar a combater o câncer, trata azia, ajuda a tratar alergias sazonais, pode ser usado para clarear os dentes dor de garganta e abafamento, e ajudar a melhorar a textura do cabelo.
<div id="natur-1579838204" class="natur-gig"></div>
<h2>O que é o vinagre de maçã?</h2>
<p class="Body">Vinagre de maçã, [ACV], é um remédio antigo usado para uma variedade de benefícios para a saúde. Embora o efeito em todos os corpos seja diferente, alguns indivíduos afirmam que experimentaram resultados dramáticos adicion
... [excerpt only; full body remains in export] ...
impressionantes das folhas de hortelã </a>
<a href="https://saudeteu.info/13-beneficios-para-a-saude-alho-poro/">13 Benefícios para a saúde de alho-poró (olhos e pele) </a>
<a href="https://saudeteu.info/11-beneficios-de-jaca/">11 Benefícios para a saúde e usos surpreendentes da jaca</a>

</div>
```

### ID 31995 (post)

Como se livrar das estrias rápido e naturalmente?

Body size: 12,309 UTF-8 bytes.

```text
<div class="g1-content-narrow g1-typography-xl entry-content">

As estrias (também conhecidas como <strong>estrias</strong> ) podem ser descritas como um dos problemas de pele onde aparecem como linhas visíveis. Eles ocorrem se houver mudanças repentinas no tamanho do corpo. Eles geralmente são vistos nas <strong>coxas, braço, nádegas, barriga, seios</strong> e <strong>áreas abdominais</strong> . Mas a questão é como se livrar das estrias rapidamente? Antes de listar as dicas, vamos entender as causas.
<h3>Causas de estrias</h3>
Se os tecidos conjuntivos são <strong>esticados</strong> acima da <strong>flexibilidade</strong> e a razão - <strong>expansão ou contração da pele</strong> , o r
... [excerpt only; full body remains in export] ...
g>Creme Preventivo de Estrias Revitol</strong> para marcas recém-formadas. Você também pode escolher <strong>o tratamento a laser</strong> ou <strong>microdermoabrasão</strong> para se livrar das estrias na pele.

</div>
<nav class="g1-nav-single">
<div class="g1-nav-single-inner"></div>
</nav>
```

### ID 45991 (post)

Que tipo de trabalho uma pessoa com transtorno bipolar deve procurar?

Body size: 10,403 UTF-8 bytes.

```text
<p>O transtorno bipolar é uma condição crônica de saúde mental caracterizada por mudanças de humor extremas e repentinas. Os sintomas do transtorno bipolar podem incluir uma fase de humor extremamente elevado conhecida como mania e episódios de depressão. Devido aos episódios maníacos, o transtorno bipolar às vezes também é conhecido como depressão maníaca ou doença bipolar. Pessoas com transtorno bipolar têm dificuldade em administrar suas tarefas diárias no trabalho ou na escola.</p>
  
 <p>Eles também acham um desafio manter seus relacionamentos. Não há cura para esta doença, mas os medicamentos podem ajudar as pessoas a controlar os sintomas. Se não forem tratadas, as condições de saúde 
... [excerpt only; full body remains in export] ...
a transtorno bipolar</li><li>Como tratar os episódios depressivos do transtorno bipolar?</li><li>Você pode ter ansiedade e transtorno bipolar ao mesmo tempo?</li><li>Os 5 principais mitos e fatos sobre o transtorno bipolar</li><li>Lidando com a incerteza dos episódios de transtorno bipolar</li></ul>
```

### ID 81718 (post)

Diabetes e ataque cardíaco: qual é a relação?

Body size: 17,048 UTF-8 bytes.

```text
<div id="health-sc-page_1-0" class="comp health-sc-page mntl-sc-page mntl-block structured-content article-content expert-content right-rail__offset lock-journey" data-sc-sticky-offset="60" data-sc-ad-label-height="24" data-sc-ad-track-spacing="100" data-sc-min-track-height="250" data-sc-max-track-height="600" data-sc-breakpoint="50em" data-sc-load-immediate="4" data-sc-content-positions="[400, 1400, 1400, 1700, 2000, 2200, 2400, 2600, 2800]" data-bind-scroll-on-start="true"><p id="mntl-sc-block_1-0" class="comp mntl-sc-block mntl-sc-block-html">Se você tem diabetes, o risco de doença cardíaca, incluindo ataque cardíaco, é maior do que para alguém sem a doença. Portanto, ter diabetes torna a
... [excerpt only; full body remains in export] ...
ador saber que você também tem um risco maior de doença cardíaca ou ataque cardíaco. No entanto, você pode ajudar a diminuir o risco de ataque cardíaco. Trabalhe com sua equipe de saúde para seguir uma dieta saudável para o coração, manter um peso saudável e praticar mais atividade física.</p></div>
```

### ID 57574 (post)

Histórico de taxas de fundos do Fed: seus máximos, mínimos e gráficos

Body size: 161,116 UTF-8 bytes.

```text
<div id="mntl-sc-page_1-0" class="comp mntl-sc-page mntl-block structured-content" data-sc-sticky-offset="90" data-sc-ad-label-height="24" data-sc-ad-track-spacing="100" data-sc-ad-bottom-offset="300" data-sc-min-track-height="250" data-sc-max-track-height="600" data-sc-breakpoint="50em" data-sc-load-immediate="4" data-sc-content-positions="[1, 1250, 1550, 1950, 2350, 2750, 3150, 3550, 3950]" data-bind-scroll-on-start="true"><p id="mntl-sc-block_1-0" class="comp mntl-sc-block mntl-sc-block-html">A Reserva Federal tende a manter a taxa dos fundos federais dentro de um ponto ideal de 2% a 5%, o que ajuda a manter uma economia saudável, mas tem havido excepções. A taxa de referência do país foi
... [excerpt only; full body remains in export] ...
as sobre dívidas, como cartões de crédito e hipotecas, mas receberá juros mais altos sobre suas poupanças e títulos.</p></div>
</div>
<div id="mm-ads-textnote_1-0" class="comp mm-ads-textnote mm-ads-gpt-adunit textnote-placeholder gpt textnote">
<div id="textnote" class="wrapper"></div>
</div></div>
```

## Storage checks

Largest exported data file: `posts.part-0009.jsonl` (33,678,457 bytes). Total exported data before reports: 1,766,508,668 bytes. No oversized file was silently omitted. JSONL uses complete-record batches near 32 MiB. Git's compressed pack size is checked separately before push.
