gpt:
Model	Quality	1024 x 1024	1024 x 1536	1536 x 1024
GPT Image 1.5	Low	$0.009	$0.013	$0.013
Medium	$0.034	$0.05	$0.05
High	$0.133	$0.2	$0.2


GPT Image 1 Mini	Low	$0.005	$0.006	$0.006
Medium	$0.011	$0.015	$0.015
High	$0.036	$0.052	$0.052

Calculating costs
Image inputs are metered and charged in tokens, just as text inputs are. How images are converted to text token inputs varies based on the model. You can find a vision pricing calculator in the FAQ section of the pricing page.

GPT-4.1-mini, GPT-4.1-nano, o4-mini
Image inputs are metered and charged in tokens based on their dimensions. The token cost of an image is determined as follows:

A. Calculate the number of 32px x 32px patches that are needed to fully cover the image (a patch may extend beyond the image boundaries; out-of-bounds pixels are treated as black.)

raw_patches = ceil(width/32)×ceil(height/32)
B. If the number of patches exceeds 1536, we scale down the image so that it can be covered by no more than 1536 patches

r = √(32²×1536/(width×height))
r = r × min( floor(width×r/32) / (width×r/32), floor(height×r/32) / (height×r/32) )
C. The token cost is the number of patches, capped at a maximum of 1536 tokens

image_tokens = ceil(resized_width/32)×ceil(resized_height/32)
D. Apply a multiplier based on the model to get the total tokens.

Model	Multiplier
gpt-5-mini	1.62
gpt-5-nano	2.46
gpt-4.1-mini	1.62
gpt-4.1-nano	2.46
o4-mini	1.72
Cost calculation examples

A 1024 x 1024 image is 1024 tokens
Width is 1024, resulting in (1024 + 32 - 1) // 32 = 32 patches
Height is 1024, resulting in (1024 + 32 - 1) // 32 = 32 patches
Tokens calculated as 32 * 32 = 1024, below the cap of 1536
A 1800 x 2400 image is 1452 tokens
Width is 1800, resulting in (1800 + 32 - 1) // 32 = 57 patches
Height is 2400, resulting in (2400 + 32 - 1) // 32 = 75 patches
We need 57 * 75 = 4275 patches to cover the full image. Since that exceeds 1536, we need to scale down the image while preserving the aspect ratio.
We can calculate the shrink factor as sqrt(token_budget × patch_size^2 / (width * height)). In our example, the shrink factor is sqrt(1536 * 32^2 / (1800 * 2400)) = 0.603.
Width is now 1086, resulting in 1086 / 32 = 33.94 patches
Height is now 1448, resulting in 1448 / 32 = 45.25 patches
We want to make sure the image fits in a whole number of patches. In this case we scale again by 33 / 33.94 = 0.97 to fit the width in 33 patches.
The final width is then 1086 * (33 / 33.94) = 1056) and the final height is 1448 * (33 / 33.94) = 1408
The image now requires 1056 / 32 = 33 patches to cover the width and 1408 / 32 = 44 patches to cover the height
The total number of tokens is the 33 * 44 = 1452, below the cap of 1536
GPT 4o, GPT-4.1, GPT-4o-mini, CUA, and o-series (except o4-mini)
The token cost of an image is determined by two factors: size and detail.

Any image with "detail": "low" costs a set, base number of tokens. This amount varies by model (see chart below). To calculate the cost of an image with "detail": "high", we do the following:

Scale to fit in a 2048px x 2048px square, maintaining original aspect ratio
Scale so that the image's shortest side is 768px long
Count the number of 512px squares in the image—each square costs a set amount of tokens (see chart below)
Add the base tokens to the total
Model	Base tokens	Tile tokens
gpt-5, gpt-5-chat-latest	70	140
4o, 4.1, 4.5	85	170
4o-mini	2833	5667
o1, o1-pro, o3	75	150
computer-use-preview	65	129
Cost calculation examples (for gpt-4o)

A 1024 x 1024 square image in "detail": "high" mode costs 765 tokens
1024 is less than 2048, so there is no initial resize.
The shortest side is 1024, so we scale the image down to 768 x 768.
4 512px square tiles are needed to represent the image, so the final token cost is 170 * 4 + 85 = 765.
A 2048 x 4096 image in "detail": "high" mode costs 1105 tokens
We scale down the image to 1024 x 2048 to fit within the 2048 square.
The shortest side is 1024, so we further scale down to 768 x 1536.
6 512px tiles are needed, so the final token cost is 170 * 6 + 85 = 1105.
A 4096 x 8192 image in "detail": "low" most costs 85 tokens
Regardless of input size, low detail images are a fixed cost.
GPT Image 1
For GPT Image 1, we calculate the cost of an image input the same way as described above, except that we scale down the image so that the shortest side is 512px instead of 768px. The price depends on the dimensions of the image and the input fidelity.

When input fidelity is set to low, the base cost is 65 image tokens, and each tile costs 129 image tokens. When using high input fidelity, we add a set number of tokens based on the image's aspect ratio in addition to the image tokens described above.

If your image is square, we add 4160 extra input image tokens.
If it is closer to portrait or landscape, we add 6240 extra tokens.
To see pricing for image input tokens, refer to our pricing page.

We process images at the token level, so each image we process counts towards your tokens per minute (TPM) limit.

For the most precise and up-to-date estimates for image processing, please use our image pricing calculator available here.

gemini modelle:
Gemini 2.5 Flash Image

Seitenverhältnis	Auflösung	Tokens
1:1	1024x1024	1290
2:3	832 × 1248	1290
3:2	1248 × 832	1290
3:4	864 × 1184	1290
4:3	1184 × 864	1290
4:5	896 × 1152	1290
5:4	1152 × 896	1290
9:16	768 × 1344	1290
16:9	1344 × 768	1290
21:9	1536 × 672	1290
Gemini 3 Pro Image Preview

Seitenverhältnis	1K-Auflösung	1.000 Tokens	2K-Auflösung	2.000 Tokens	4K-Auflösung	4K-Tokens
1:1	1024x1024	1.120	2.048 x 2.048	1.120	4096 x 4096	2000
2:3	848 × 1264	1.120	1696 × 2528	1.120	3392 × 5056	2000
3:2	1264 × 848	1.120	2528 × 1696	1.120	5056 × 3392	2000
3:4	896 × 1200	1.120	1792 × 2400	1.120	3584 × 4800	2000
4:3	1200 × 896	1.120	2400 × 1792	1.120	4800 × 3584	2000
4:5	928 × 1152	1.120	1856 × 2304	1.120	3712 × 4608	2000
5:4	1152 × 928	1.120	2304 × 1856	1.120	4608 × 3712	2000
9:16	768 × 1376	1.120	1536 × 2752	1.120	3072 × 5504	2000
16:9	1376 × 768	1.120	2752 × 1536	1.120	5504 × 3072	2000
21:9	1584 × 672	1.120	3168 × 1344	1.120	6336 × 2688	2000

Gemini 3 Pro Image Preview 🍌
gemini-3-pro-image-preview
In Google AI Studio ausprobieren

Unser natives Modell für die Bildgenerierung, das für Geschwindigkeit, Flexibilität und Kontextverständnis optimiert ist. Texteingabe und -ausgabe kosten dasselbe wie Gemini 3 Pro.

Vorschaumodelle können sich ändern, bevor sie stabil werden, und haben restriktivere Ratenlimits.

Standard
Batch
Kostenlose Stufe	Kostenpflichtige Stufe, pro 1 Million Tokens in USD
Eingabepreis	Nicht verfügbar	2,00 $ (Text/Bild),
entspricht 0,0011 $pro Bild*
Ausgabepreis	Nicht verfügbar	12,00 $ (Text und Denken)
120,00 $ (Bilder)
entspricht 0,134 $pro 1K-/2K-Bild**
und 0,24 $pro 4K-Bild**
Zur Verbesserung unserer Produkte	Ja	Nein
* Die Bildeingabe ist auf 560 Tokens oder 0,0011 $pro Bild festgelegt.

** Die Bildausgabe wird mit 120 $pro 1.000.000 Tokens berechnet. Für Ausgabebilder mit einer Größe von 1024 × 1024 Pixel (1K) bis 2048 × 2048 Pixel (2K) werden 1120 Tokens verwendet, was 0,134 $pro Bild entspricht. Ausgabebilder mit einer Größe von bis zu 4096 × 4096 Pixeln (4K) verbrauchen 2.000 Tokens und entsprechen 0,24 $pro Bild.


Gemini 2.5 Flash Image 🍌
gemini-2.5-flash-image
In Google AI Studio ausprobieren

Unser natives Modell für die Bildgenerierung, das für Geschwindigkeit, Flexibilität und Kontextverständnis optimiert ist. Die Preise für Texteingabe und -ausgabe entsprechen denen von 2.5 Flash.

Vorschaumodelle können sich ändern, bevor sie stabil werden, und haben restriktivere Ratenlimits.

Standard
Batch
Kostenlose Stufe	Kostenpflichtige Stufe, pro 1 Million Tokens in USD
Eingabepreis	Nicht verfügbar	0,30 $ (Text / Bild)
Ausgabepreis	Nicht verfügbar	0,039 $ pro Bild*
Zur Verbesserung unserer Produkte	Ja	Nein
[*] Die Bildausgabe kostet 30 $pro 1.000.000 Tokens. Ausgabebilder mit einer Größe von bis zu 1.024 × 1.024 Pixel verbrauchen 1.290 Tokens und kosten 0,039 $pro Bild.