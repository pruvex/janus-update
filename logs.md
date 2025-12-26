10zlAjtTEzXRUNydpKV2JydkeWGY87LdhbzHOgpFrVFimjbLJzi42s6BGuWUv/SEpS5tYml6MS2qFyaS7lwO95LvrCV4L8lhxWKzBHuVYvaTnUBjL1xpEiqsLHgEg53RTbiJ2bmlasweoawqaUrxSm7xAEYinpXR5tKEGJ0DSOVSyabIe655XAxUbQcTrgG+LiOvrafckDZ/Yp8fEd/E/1HkWErrr83zfszOh436OjDCbf3s75yvqUaObh0xiRtZAAACFklEQVSZkpHAqLAk3V+bUXFRugRD8jsji2/9Dz2K8TKSZ7OO0QmyOGkSkMHm8iLZTDGjGe70CDeTDBIvJGHtNBKjzUbORnivFFDIKZuR0sS2MurRcjGQJcMJy27zhbNRmpkR2Xw3InRse1avYMIb0+RHJzERqfVAi+IJ6EWb/IcVP4gGnANwx0Vw72CYsfddKHrzNEPvBmgNynNxWNwoOzLJbO+ClNRaRbXmsK1B+zFAfi7Glj+9/SG14fp8WrhqE8MeV+j8GHUsqPS9hKpYiLay4mxwPgTAVlZvgqpVnDGUSFI/nXc0jywTAHhXSFKJMt4D53p+0d3qA4/gRhIsx9agd9nwnwRq9udjjd5S0OcefBag80XnyxujbuFiIiv+9iNGTMMcN/NbBoNSrgnV11GHtglr1MxRVbAdGjwQ/yXHpIBukpVYpNK6jIZTSOutW7YY0JU3q+p5o2vTShXXcCKqNphmiEISe5ekBlMZoPUra8tgLsI8C3YWJAxx9+OhK7nTXWhq4KgrgAQtWFuHzDJXuiG9/LTY9rxlTMS7FjTmBRebI7vJf+4LW7a0B+KqsN8t3U3O7VPrBJSqeCR9b/UTQdcB/FiNeI1NuZubzkxqF8wakhaZO3PBO2zwb95mCAdNK9dzVuM4qZT2xZNZZ0l8/IxbTaPboYaOVEkjw3TLjzrCsGN5TCTdMZsD+WfWheXnl1/+P61GZa8iTzMUAAAAAElFTkSuQmCC"
[start-backend-only]                 }
[start-backend-only]               }
[start-backend-only]             ],
[start-backend-only]             "role": "model"
[start-backend-only]           },
[start-backend-only]           "finish_reason": "STOP",
[start-backend-only]           "index": 0
[start-backend-only]         }
[start-backend-only]       ],
[start-backend-only]       "usage_metadata": {
[start-backend-only]         "prompt_token_count": 4,
[start-backend-only]         "candidates_token_count": 1290,
[start-backend-only]         "total_token_count": 1294
[start-backend-only]       },
[start-backend-only]       "model_version": "gemini-2.5-flash-image"
[start-backend-only]     }),
[start-backend-only] )
[start-backend-only] 2025-12-25 19:44:21 - janus_backend - [INFO] - Image saved from bytes to C:\Users\pruve\AppData\Local\JanusDev\Janus Projekt\images\ein-apfel-41-25-12-25.png
[start-backend-only] 2025-12-25 19:44:21 - janus_backend - [ERROR] - Error generating image with Gemini (attempt failed): _calculate_and_log_cost() got an unexpected keyword argument 'image_size'
[start-backend-only] Traceback (most recent call last):
[start-backend-only]   File "C:\KI\Janus-Projekt\backend\llm_providers\capabilities\gemini_image_generation.py", line 181, in generate_image
[start-backend-only]     usage, cost = _calculate_and_log_cost(model, custom_prompt=prompt, **cost_calculation_kwargs)
[start-backend-only]                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
[start-backend-only] TypeError: _calculate_and_log_cost() got an unexpected keyword argument 'image_size'
[start-backend-only] Traceback (most recent call last):
[start-backend-only]   File "C:\KI\Janus-Projekt\backend\llm_providers\capabilities\gemini_image_generation.py", line 181, in generate_image
[start-backend-only]     usage, cost = _calculate_and_log_cost(model, custom_prompt=prompt, **cost_calculation_kwargs)
[start-backend-only]                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
[start-backend-only] TypeError: _calculate_and_log_cost() got an unexpected keyword argument 'image_size'
[start-backend-only] 2025-12-25 19:44:23 - janus_backend - [DEBUG] - Gemini image_config before API call: {}
[start-backend-only] 2025-12-25 19:44:23 - janus_backend - [DEBUG] - Gemini request_options before API call: {}
[start-backend-only] 2025-12-25 19:44:23 - janus_backend - [INFO] - Calling Gemini image model 'gemini-2.5-flash-image' with prompt: 'ein apfel' and reference image: False
[start-backend-only] 2025-12-25 19:44:23 - janus_backend - [DEBUG] - Gemini API call contents: [{'role': 'user', 'parts': [{'text': 'ein apfel'}]}]