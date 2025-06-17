insert into public.product_type_rules 
(id, type_id, rule)
values
('2061a06b-9f4b-4dac-819d-3127e68f94e6', '5f7d5346-5c7f-449f-83da-47117b7d2336', 'For "Cucumber", the default variety is "Naked" if no other value is provided. If the value is "Cucumber", it should be considered as "Naked".');



-- Add alias 'Punt paprika' for Pointed pepper
INSERT INTO public.product_attributes_value_aliases
(id, alias_type_id, value_id, alias)
values
('2dd8f394-89d4-429c-8188-476a933a866d', 'f3d37d28-303b-429c-baea-e8635838faad', '60653488-0bbf-4f48-8bb0-7911b8c2481d', 'Punt Paprika'),
('6d7b96a5-c352-4b3c-b1e6-8f35650285f6', 'f3d37d28-303b-429c-baea-e8635838faad', '60653488-0bbf-4f48-8bb0-7911b8c2481d', 'Groenpunt Paprika'),
('538cc278-5741-46b8-997e-d40b3bb860af', 'f3d37d28-303b-429c-baea-e8635838faad', '60653488-0bbf-4f48-8bb0-7911b8c2481d', 'Geelpunt Paprika'),
('594cc301-aea5-46da-acbc-d892d4d0e579', 'f3d37d28-303b-429c-baea-e8635838faad', '60653488-0bbf-4f48-8bb0-7911b8c2481d', 'Roodpunt Paprika'),
('d54d483e-815b-422e-acf7-6e14289acb47', 'f3d37d28-303b-429c-baea-e8635838faad', '60653488-0bbf-4f48-8bb0-7911b8c2481d', 'Oranjepunt Paprika');

