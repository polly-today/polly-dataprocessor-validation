
select * from pieces order by name asc; --created_at desc;
select * from sizes order by name asc; --created_at desc;

-- Update masterdata for product types
delete from offers where product_sub_variety_id = 'c39214dd-5e5c-4eff-83b6-b3d4a6d704c1';
delete from offers where product_variety_id = '19b41116-5126-4760-b9e6-65f402009ac6';
delete from product_sub_varieties  where id = 'c39214dd-5e5c-4eff-83b6-b3d4a6d704c1';
delete from product_varieties  where id = '19b41116-5126-4760-b9e6-65f402009ac6';
delete from offers where size_id = 'ae3de7a8-fc5a-44e1-96cc-e8bf0d474071';
delete from product_type_sizes where size_id = 'ae3de7a8-fc5a-44e1-96cc-e8bf0d474071';
delete from public.product_attributes_value_aliases where id in ('d35014b0-5fc7-455e-a30f-5f595f24bfb7');
DELETE FROM public.sizes WHERE id IN ('ae3de7a8-fc5a-44e1-96cc-e8bf0d474071');
delete from public.product_type_sizes where id = 'd0eeedb1-140a-48d7-9940-bdd77fd06726';
delete from supplier_rules where id in ('73252ba9-e73e-4e6d-9a77-240035a65a98', 'f4d468b2-2ddd-4225-aab0-49c19025708d', '96a47ff9-eb15-4276-a280-a9984f85de9a');

select * from product_types

-- Insert new product types and varieties
insert into public.product_types
(id, name, group_id)
values
('85cfea73-513e-4d2e-b2ac-ed2154468695', 'Classic Tomato Mix', '2e8f1f6f-2f34-466d-82bf-803de8eb1ceb'),
('3ddd2ea4-5f0f-47de-8a70-2cd1ddf409b1', 'Cherry Plum Vine Tomato', '2e8f1f6f-2f34-466d-82bf-803de8eb1ceb');
insert into public.product_varieties
(id, name, type_id, created_at, updated_at)
values
('6e416f61-054a-4847-911e-fe9fed6306d0', 'unspecified', (select id from product_types where name = 'Classic Tomato Mix'), now(), now()),
('782bc741-2e3a-4a1a-ac8e-2f406e78b69a', 'unspecified', (select id from product_types where name = 'Cherry Plum Vine Tomato'), now(), now()),
('5d9808de-bda5-4f87-a1ef-8b2ccc54610d', 'Round Mix', (select id from product_types where name = 'Zucchini'), now(), now());
insert into public.product_sub_varieties
(id, name, variety_id, created_at, updated_at)
values
('d4e4109f-cd96-466e-b740-e13d98293fd8', 'unspecified', '6e416f61-054a-4847-911e-fe9fed6306d0', now(), now()),
('6556e4e3-133e-456d-bf29-e147ed5347c1', 'unspecified', '782bc741-2e3a-4a1a-ac8e-2f406e78b69a', now(), now()),
('21a7a6b8-a3d7-4e74-b23b-f89e6f92a996', 'unspecified', '5d9808de-bda5-4f87-a1ef-8b2ccc54610d', now(), now());
-- Add pieces relationships for the new product types
insert into public.product_type_pieces
(id, product_type_id, piece_id)
values
('4e45db4a-3124-4e1b-aeb9-2b9bc7153a3d', '85cfea73-513e-4d2e-b2ac-ed2154468695', (select id from pieces where name = 'unspecified')),
('5d6906ff-d41c-40a2-9759-81aba1434e17', '3ddd2ea4-5f0f-47de-8a70-2cd1ddf409b1', (select id from pieces where name = 'unspecified'));
-- Add sizes relationships for the new product types
insert into public.product_type_sizes
(id, product_type_id, size_id)
values
('82e079c4-3e51-4b5a-bfb1-63ece40e3f73', '85cfea73-513e-4d2e-b2ac-ed2154468695', (select id from sizes where name = 'unspecified')),
('ab28a224-f6b6-4630-bf5b-72b5f3d3b476', '3ddd2ea4-5f0f-47de-8a70-2cd1ddf409b1', (select id from sizes where name = 'unspecified'));
-- Add brand relationships for the new product types
insert into public.product_type_brands
(id, product_type_id, brand_id)
values
('14846d0b-8657-4a76-a1c7-ccd431004a9a', '85cfea73-513e-4d2e-b2ac-ed2154468695', (select id from brands where name = 'unspecified')),
('29bbd857-3512-4bc0-8748-baa138ba72e9', '3ddd2ea4-5f0f-47de-8a70-2cd1ddf409b1', (select id from brands where name = 'unspecified'));

-- Insert sizes
insert into public.sizes
(id, name, created_at, updated_at)
values
('f4557b81-03be-4889-970d-7bfee85b8d9d', '72+', now(), now()),
('33da09c1-7fed-47b4-ae8b-5dd20c4f5a7b', '82+', now(), now()),
('a4ed2289-bdb6-4d64-b2c8-ed47306622f7', '92+', now(), now()),
('b97a82aa-e165-4060-bcfd-836274c85a61', '102+', now(), now()),
('98ba6216-3379-48e3-a643-3175d845eabc', '2kg/+', now(), now()),
('4b8d120c-165e-4edc-82ce-c3d435be7e8e', '1.5kg/+', now(), now()); 

-- Insert pieces
insert into public.pieces
(id, name, created_at, updated_at)
values
('b34ef4f7-3923-41cc-a226-b6105924295c', '12x100g', now(), now()),
('b6f7d6cd-eb68-40dc-8fc6-c3c46276a556', '24x250g', now(), now());

-- Add product type rules
select * from product_type_rules;
insert into public.product_type_rules 
(id, type_id, rule)
values
('99134496-bdbd-4df5-9f66-fc13012288d6', 'b0582ea7-b613-4ab2-85f8-5847525ef0b7', 'If the input only mentions "Cherry" without any additional descriptors (e.g., "plum", "vine", "plum vine"), assign product_type = "Cherry Tomato".'),
('b0582ea7-b613-4ab2-85f8-5847525ef0b7', 'b0582ea7-b613-4ab2-85f8-5847525ef0b7', 'For "Cherry Tomato", if pieces are specified in the format of multiple units of 250g (e.g., "9x250g", "8x250g", etc.), and the variety does not already include a specific form (e.g., Triangle, Shaker, etc.), default to a "Punnet" variety. Combine the inferred color (Red, Yellow, Mix — defaulting to Red if unspecified) with the form "Punnet" to assign the correct variety (e.g. "9x250g" → "Red Punnet", "8x250g Mix" → "Mix Punnet").'),
('db021c14-8614-4555-9fe6-36cf1920478f', 'de6d3dbe-8037-41a7-87c3-f7ce56f6f47e', 'For "Cherry Plum Tomato", if pieces are specified in the format of multiple units of 500g and the variety does not already indicate a specific packaging form (e.g., Flowpack, Punnet, etc.), default to a "Bucket" variety. Combine the inferred color (Red, Yellow, Mix — defaulting to Red if unspecified) with the form "Bucket" to assign the correct variety (e.g. "10x500g" → "Red Bucket", "8x500g Mix" → "Mix Bucket").'),
('927a0918-db6b-4a30-8695-676be9a08414', 'e8bb2819-5c18-4751-9502-9e9fc4843476', 'For "Cauliflower", if no variety or product-level packaging (e.g., filmed/naked) is mentioned, default to "White Naked". If the input mentions product-level film packaging (e.g., "foly", "filmed") and no color or variety is specified, assign variety = "White Filmed". If a color or type is explicitly mentioned (e.g., "Purple", "Orange", "Romanesco"), use that as the variety without appending any packaging descriptors — even if filmed is mentioned.'),
('6e0a1341-baef-4128-ab4f-397f32b64eae', 'db2a67da-ffbc-4cb8-83ea-423d8684b44f', 'For "Broccoli", the defaults are "Naked" and "Green". Use these defaults to select the most specific matching variety from the allowed options (e.g., "Broccoli filmed" → "Green Filmed", "Broccoli purple" → "Purple Naked").'),
('76663c21-0e82-4139-8fc8-ae3219eddff7', 'b3e3e08e-19db-4bcb-b604-f9d5bf6b8ab1', 'For "Zucchini", If no color or shape is explicitly mentioned in the input, default to variety = "Green". Only extract other varieties (e.g., "White", "Yellow", "Round Green", "Round Yellow") when they are explicitly stated in the text.'),
('2061a06b-9f4b-4dac-819d-3127e68f94e6', '5f7d5346-5c7f-449f-83da-47117b7d2336', 'For "Cucumber", the default variety is "Naked" if no other value is provided. If the value is "Cucumber", it should be considered as "Naked".'),


-- Add aliases for Pointed pepper
INSERT INTO public.product_attributes_value_aliases
(id, alias_type_id, value_id, alias)
values
('2dd8f394-89d4-429c-8188-476a933a866d', 'f3d37d28-303b-429c-baea-e8635838faad', '60653488-0bbf-4f48-8bb0-7911b8c2481d', 'Punt Paprika'),
('6d7b96a5-c352-4b3c-b1e6-8f35650285f6', 'f3d37d28-303b-429c-baea-e8635838faad', '60653488-0bbf-4f48-8bb0-7911b8c2481d', 'Groenpunt Paprika'),
('538cc278-5741-46b8-997e-d40b3bb860af', 'f3d37d28-303b-429c-baea-e8635838faad', '60653488-0bbf-4f48-8bb0-7911b8c2481d', 'Geelpunt Paprika'),
('594cc301-aea5-46da-acbc-d892d4d0e579', 'f3d37d28-303b-429c-baea-e8635838faad', '60653488-0bbf-4f48-8bb0-7911b8c2481d', 'Roodpunt Paprika'),
('d54d483e-815b-422e-acf7-6e14289acb47', 'f3d37d28-303b-429c-baea-e8635838faad', '60653488-0bbf-4f48-8bb0-7911b8c2481d', 'Oranjepunt Paprika');

-- Add aliases for Sizes
INSERT INTO public.product_attributes_value_aliases
(id, alias_type_id, value_id, alias)
values
('609c0d79-fb1a-4139-9a11-c6d80ef4d309', 'c6fac811-2330-43f6-9ce6-ecc86d1e8c48', (select id from sizes where name = 'G'), 'Grof'),
('cdcbdd55-94b4-48f9-a40c-c1365d73d923', 'c6fac811-2330-43f6-9ce6-ecc86d1e8c48', (select id from sizes where name = 'G'), 'L'),
('2c2aceda-f22f-43d5-b016-da2e1b8b3df1', 'c6fac811-2330-43f6-9ce6-ecc86d1e8c48', (select id from sizes where name = 'P'), 'S');

-- Add pieces relationships to Green Cabbage
insert into public.product_type_pieces
(id, product_type_id, piece_id)
values
('1f297040-f1e5-4c67-966a-e239c6bf146d', 'd3180d15-86bc-4ffc-abae-8477f23a0c31', (select id from pieces where name = '9-10stk')),
('722640db-e74a-4f4f-b68c-7973491f8878', 'd3180d15-86bc-4ffc-abae-8477f23a0c31', (select id from pieces where name = '7-10stk')),
('18203fec-46d1-4c10-91d8-dbe89a853b73', 'd3180d15-86bc-4ffc-abae-8477f23a0c31', (select id from pieces where name = '7stk')),
('ac875600-e152-4f91-bdbd-2a375f09ef0b', 'd3180d15-86bc-4ffc-abae-8477f23a0c31', (select id from pieces where name = '5-7stk')),
('7889facc-e082-4501-91ec-3b4798d7d03b', 'd3180d15-86bc-4ffc-abae-8477f23a0c31', (select id from pieces where name = '5-6stk')),
('8f67a013-f2c2-4255-bd30-85c2b6f629a5', 'd3180d15-86bc-4ffc-abae-8477f23a0c31', (select id from pieces where name = '10-15stk')),
('116f03c7-24d7-4197-956f-2b8d23c74e57', 'd3180d15-86bc-4ffc-abae-8477f23a0c31', (select id from pieces where name = '12-15stk')),
('6705d38f-6b96-4671-a276-61d5acb987b4', 'd3180d15-86bc-4ffc-abae-8477f23a0c31', (select id from pieces where name = '12-13stk')),
('d900c030-b936-482e-a616-bb933c0a5c50', 'd3180d15-86bc-4ffc-abae-8477f23a0c31', (select id from pieces where name = '8-11stk')),
('08516ac1-1aed-489b-9862-a9bc48794a47', 'd3180d15-86bc-4ffc-abae-8477f23a0c31', (select id from pieces where name = '12-20stk'));

-- Add sizes relationships to Green Cabbage
insert into public.product_type_sizes
(id, product_type_id, size_id)
values
('212fedf3-39e3-496c-8db3-31326c005840', 'd3180d15-86bc-4ffc-abae-8477f23a0c31', (select id from sizes where name = '2kg/+')),
('b326327d-cf88-4a5d-9c0e-d91b106a2e3d', 'd3180d15-86bc-4ffc-abae-8477f23a0c31', (select id from sizes where name = '1.5kg/+'));

-- Add pieces relationships to Red Cabbage
insert into public.product_type_pieces
(id, product_type_id, piece_id)
values
('4f9e6a6e-40c7-4a3a-a580-1dedc1657e58', '8fea368c-9249-4cb0-88fb-f3804fd3b9e0', (select id from pieces where name = '9-10stk')),
('14d86e21-d433-48b1-af37-c6c40596343c', '8fea368c-9249-4cb0-88fb-f3804fd3b9e0', (select id from pieces where name = '6-8stk')),
('96512545-c054-46b6-8822-de49b48ec3a8', '8fea368c-9249-4cb0-88fb-f3804fd3b9e0', (select id from pieces where name = '5-6stk')),
('f6f778bb-828e-4d48-bf3c-f800f3ffb2fd', '8fea368c-9249-4cb0-88fb-f3804fd3b9e0', (select id from pieces where name = '12-15stk')),
('2b105bc2-803a-4479-8d90-c67d37380611', '8fea368c-9249-4cb0-88fb-f3804fd3b9e0', (select id from pieces where name = '7-10stk'));

-- Add sizes relationships to Red Cabbage
insert into public.product_type_sizes
(id, product_type_id, size_id)
values
('732157c4-7d59-44cc-a0c9-0f8669844da6', '8fea368c-9249-4cb0-88fb-f3804fd3b9e0', (select id from sizes where name = '2kg/+')),
('838da334-78f7-4faf-83c9-2dd44d25dbf7', '8fea368c-9249-4cb0-88fb-f3804fd3b9e0', (select id from sizes where name = '1.5kg/+'));

-- Add pieces relationships to Savoy Cabbage
insert into public.product_type_pieces
(id, product_type_id, piece_id)
values
('a9eae759-502f-4717-96fb-1e54ccaad611', 'eb074dc8-f3da-4dec-a31c-bface2a235ad', (select id from pieces where name = '2x350kg'));

-- Add sizes relationships to Brussels Sprouts
insert into public.product_type_sizes
(id, product_type_id, size_id)
values
('133df1d3-ba35-4e46-9aba-930448f23db2', '98a403e8-fc34-4844-8044-f6456dd6c687', (select id from sizes where name = '30-35'));

-- Add pieces relationships to Broccoli
insert into public.product_type_pieces
(id, product_type_id, piece_id)
values
('0e7a39d3-fc0e-40b3-9a0b-8cbbf1d0483e', 'db2a67da-ffbc-4cb8-83ea-423d8684b44f', (select id from pieces where name = '24x250g')),
('d6d15e0a-ce99-4db6-915e-712c1f35d6cf', 'db2a67da-ffbc-4cb8-83ea-423d8684b44f', (select id from pieces where name = '12x200g'));

-- Add pieces relationships to Cauliflower
insert into public.product_type_pieces
(id, product_type_id, piece_id)
values
('3d05b0bf-9c28-44ec-93c9-1818c69a14ae', 'e8bb2819-5c18-4751-9502-9e9fc4843476', (select id from pieces where name = '11stk'));

-- Add sizes relationships to Chinese Cabbage
insert into public.product_type_sizes
(id, product_type_id, size_id)
values
('c43c3b10-67e8-43f7-b9cc-9c2bac5e8faa', '84736521-4a1a-4127-8177-422b7432acb2', (select id from sizes where name = '600g/+')),
('474a1dd3-1b89-412e-b3e6-deb94bcd0084', '84736521-4a1a-4127-8177-422b7432acb2', (select id from sizes where name = '700g/+'));

-- Add pieces relationships to Kohlrabi
insert into public.product_type_pieces
(id, product_type_id, piece_id)
values
('a3ea0246-5304-4aa4-9d7a-be3d91bda0fa', 'f4aa68e3-078f-413a-b691-5351915dd39a', (select id from pieces where name = '12stk')),
('b6c27165-9882-4283-b5db-bd96e6b5a961', 'f4aa68e3-078f-413a-b691-5351915dd39a', (select id from pieces where name = '20stk')),
('bfa1101b-1b15-4e54-8319-ae98f6eedba8', 'f4aa68e3-078f-413a-b691-5351915dd39a', (select id from pieces where name = '8-12stk')),
('f3c6fb22-7416-4138-a0bf-77fac603e9d6', 'f4aa68e3-078f-413a-b691-5351915dd39a', (select id from pieces where name = '15stk'));

-- Add sizes relationships to Pointed Cabbage Green
insert into public.product_type_sizes
(id, product_type_id, size_id)
values
('d3b0f1c2-4a5e-4c8f-8b1c-2f3d4e5f6a7b', 'e6b527e0-1906-45a7-9dcf-04f1d78a75d6', (select id from sizes where name = '400g/+')),
('f4c5d6e7-8a9b-4c0d-b1e2-3f4a5b6c7d8e', 'e6b527e0-1906-45a7-9dcf-04f1d78a75d6', (select id from sizes where name = '500g/+')),
('a5d6e7f8-9a0b-4c1d-b2e3-4f5a6b7c8d9e', 'e6b527e0-1906-45a7-9dcf-04f1d78a75d6', (select id from sizes where name = '600-1200'));

-- Add pieces relationships to Pointed Cabbage Green
insert into public.product_type_pieces
(id, product_type_id, piece_id)
values
('b7e1a8c2-2c3e-4e2b-9e3a-1a2b3c4d5e6f', 'e6b527e0-1906-45a7-9dcf-04f1d78a75d6', (select id from pieces where name = '9-11stk')),
('c8f2b9d3-3d4f-5f3c-0f4b-2b3c4d5e6f7a', 'e6b527e0-1906-45a7-9dcf-04f1d78a75d6', (select id from pieces where name = '2x350kg')),
('d9a3c0e4-4e5a-6a4d-1a5c-3c4d5e6f7a8b', 'e6b527e0-1906-45a7-9dcf-04f1d78a75d6', (select id from pieces where name = '10stk')),
('e0b4d1f5-5f6b-7b5e-2b6d-4d5e6f7a8b9c', 'e6b527e0-1906-45a7-9dcf-04f1d78a75d6', (select id from pieces where name = '12stk'));

-- Add sizes relationships to Radish
insert into public.product_type_sizes
(id, product_type_id, size_id)  
values
('bd7226d4-108a-4f57-b59a-6d31d7d7c32b', 'a6d27654-912e-47d3-818b-b31a2c13b3f3', (select id from sizes where name = 'XL'));

-- Add pieces relationships to Radish
insert into public.product_type_pieces
(id, product_type_id, piece_id)
values
('f1e2d3c4-5b6a-7d8e-9f0a-1b2c3d4e5f6a', 'a6d27654-912e-47d3-818b-b31a2c13b3f3', (select id from pieces where name = '30stk')),
('a2b3c4d5-6e7f-8a9b-0c1d-2e3f4a5b6c7d', 'a6d27654-912e-47d3-818b-b31a2c13b3f3', (select id from pieces where name = '5x2.5kg'));

-- Add sizes relationships to Onion
insert into public.product_type_sizes
(id, product_type_id, size_id)
values
('d0eeedb1-140a-48d7-9940-bdd77fd06726', 'b34ef4f7-3923-41cc-a226-b6105924295c', (select id from sizes where name = '70+'));

-- Add pieces relationships to Shallot
insert into public.product_type_pieces
(id, product_type_id, piece_id)
values
('c39214dd-5e5c-4eff-83b6-b3d4a6d704c1', '0f83f0f8-a944-47f8-87d6-fb5236efbbd1', (select id from pieces where name = '20x250g'));

-- Add pieces relationships to Chili Pepper
insert into public.product_type_pieces
(id, product_type_id, piece_id)
values
('19b41116-5126-4760-b9e6-65f402009ac6', '47c48722-a4de-4529-a838-b9e120010ad1', (select id from pieces where name = '10x200g')),
('c39215dd-5e5c-4eff-83b6-b3d4a6d704c6', '47c48722-a4de-4529-a838-b9e120010ad1', (select id from pieces where name = '12x100g'));

-- Add pieces relationships to Celeriac
insert into public.product_type_pieces
(id, product_type_id, piece_id)
values
('eb3dfd1f-0731-4969-b845-ae13f29e89ca', '4b62cc26-e815-4e20-ab3a-2d59ed9ec181', (select id from pieces where name = '10stk')),
('1de9337f-ed52-431d-a5d1-732060463b39', '4b62cc26-e815-4e20-ab3a-2d59ed9ec181', (select id from pieces where name = '8-12stk')),
('b4f2fd7a-a3c8-42c3-a965-2fe09cfd9a25', '4b62cc26-e815-4e20-ab3a-2d59ed9ec181', (select id from pieces where name = '12-15stk')),
('dd519298-ca8f-4ed6-896a-53f4110a29bc', '4b62cc26-e815-4e20-ab3a-2d59ed9ec181', (select id from pieces where name = '12stk')),
('9b03ded7-3656-46a5-976d-033520c5189b', '4b62cc26-e815-4e20-ab3a-2d59ed9ec181', (select id from pieces where name = '5stk')),
('2edc7e87-3890-470e-8739-9d88f077f33b', '4b62cc26-e815-4e20-ab3a-2d59ed9ec181', (select id from pieces where name = '6stk')),
('6c16c9a3-f142-4dfd-b99c-90053c67a382', '4b62cc26-e815-4e20-ab3a-2d59ed9ec181', (select id from pieces where name = '8stk')),
('43926afd-8846-4ebd-a9b5-f17e25c3aca4', '4b62cc26-e815-4e20-ab3a-2d59ed9ec181', (select id from pieces where name = '15stk')),
('e6e265a5-b113-4b27-928c-ed67b6c108de', '4b62cc26-e815-4e20-ab3a-2d59ed9ec181', (select id from pieces where name = '20stk'));

-- Add pieces relationships to Cucumber
insert into public.product_type_pieces
(id, product_type_id, piece_id)
values
('3164d0cb-4c96-43ad-89c0-8b578de7285c', '5f7d5346-5c7f-449f-83da-47117b7d2336', (select id from pieces where name = '32stk')),
('48696548-82a9-490d-a799-acf2294b0ba0', '5f7d5346-5c7f-449f-83da-47117b7d2336', (select id from pieces where name = '24stk')),
('3652c2d6-e6fd-4a9c-9bb9-e0425f0aad82', '5f7d5346-5c7f-449f-83da-47117b7d2336', (select id from pieces where name = '30stk')),
('a1cc1478-6bdc-4893-844f-03a709cdb0de', '5f7d5346-5c7f-449f-83da-47117b7d2336', (select id from pieces where name = '36stk')),
('2487782e-21b6-40c7-b637-21f027e9fdcd', '5f7d5346-5c7f-449f-83da-47117b7d2336', (select id from pieces where name = '42stk')),
('cbc1fb52-e92c-443b-80aa-897fc07c260b', '5f7d5346-5c7f-449f-83da-47117b7d2336', (select id from pieces where name = '48stk')),
('78b8f503-d51a-480f-bde5-69a460e053ed', '5f7d5346-5c7f-449f-83da-47117b7d2336', (select id from pieces where name = '22stk'));

-- Add sizes relationships to Beef Tomato
insert into public.product_type_sizes
(id, product_type_id, size_id)
values
('a40f8931-59e2-4937-a324-dafafc050c2b', '374f49d7-0b89-494b-af66-f619ff516dfc', (select id from sizes where name = '72+')),
('61509b31-0346-4709-98c1-d2e4506c7bb7', '374f49d7-0b89-494b-af66-f619ff516dfc', (select id from sizes where name = '82+')),
('f78c7357-f01f-4bfb-bdbd-00ead9592e56', '374f49d7-0b89-494b-af66-f619ff516dfc', (select id from sizes where name = '92+')),
('dbfaddde-7653-49a3-b257-ea3e654071e8', '374f49d7-0b89-494b-af66-f619ff516dfc', (select id from sizes where name = '102+'));

-- Add sizes relationships to Cherry Vine Tomato
insert into public.product_type_sizes
(id, product_type_id, size_id)
values
('be13a0ec-33a2-4ef0-a8d8-e922c05fd662', '1a8dd712-7bf2-44d3-aeda-d354e5e1c3d6', (select id from sizes where name = '25-30'));

-- Add supplier rules for Fossa Eugenia
insert into public.supplier_rules
(id, supplier_id, rule)
values
('1e996769-d63f-44c8-9020-25d2a40fa485', '41420926-6295-4ac8-8640-e6d29f54185b', 'If multiple values for pieces are written in the form "X of Y stuks" (e.g., "12 of 15 stuks"), treat these as separate values and split into two separate offers: one with pieces = "12stk" and one with pieces = "15stk". However, if the input uses a range format such as "12-15 stuks", interpret this as a single range value and do not split into 2 offers: pieces = "12-15stk".');

select * from product_type_pieces
left join product_types on product_types.id = product_type_pieces.product_type_id
left join pieces on pieces.id = product_type_pieces.piece_id
--where product_types.name = 'Broccoli'

select * from product_type_sizes
left join product_types on product_types.id = product_type_sizes.product_type_id
left join sizes on sizes.id = product_type_sizes.size_id
where product_types.name = 'Pointed Cabbage Green'
