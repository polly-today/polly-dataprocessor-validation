-- IGNORE THIS FILE 

select * from dataprocessor_sqs_messages 
where extracted_email_sender = 't.hendriks@frankort.nl'
order by created_at desc
limit 100;



select * from dataprocessor_sqs_messages where id = '2f827436-130d-4b48-85a9-3751dc1d0a66'


SELECT id,
       message,
       created_at,
       updated_at,
       status,
       source_type_id,
       error_msg,
       processed_at,
       aws_request_id,
       aws_function_name,
       process_message,
       raw_product_info,
       prompt,
       extracted_email_sender,
       extracted_email_subject,
       extracted_email_datetime
FROM public.dataprocessor_sqs_messages
ORDER BY created_at DESC
LIMIT 100;


select * from dataprocessor_prompts
where dataprocessor_sqs_message_id = '2f827436-130d-4b48-85a9-3751dc1d0a66'
order by created_at desc
limit 100;



select 
s.name as supplier_name,
m.extracted_email_sender as sender,
m.extracted_email_datetime as "date",
m.extracted_email_subject as subject,
e.product_type as "type",
e.product_variety as variety,
e.product_sub_variety as sub_variety,
e.size,
e.piece,
e.brand,
e.package_type,
e.class,
e.origin_country_code,
e.net_weight,
e.quantity_per_pallet,
e.price,
e.remarks,
e.source
from dataprocessor_sqs_messages m
inner join dataprocessor_sqs_messages_extracted_data e on m.id = e.dataprocessor_sqs_messages_id
inner join suppliers s on e.supplier_id = s.id
where m.id = '2f827436-130d-4b48-85a9-3751dc1d0a66'


________________________________Van: Thei Hendriks <t.hendriks@frankort.nl>Verzonden: vrijdag 21 maart 2025 06:07Aan: Dagprijzen Komkommers <Dagprijzenkomkommers@frankort.nl>; Commercie_Venlo <Commercie_Venlo@frankort.nl>Onderwerp: Dagprijzen komkommers.xlsx​​​​​[cid:image669829.jpg@60607668.55F6C879]Thei HendriksFrankort & Koning B.V.[cid:image210757.png@17EEFD66.7A82DDDF]+31 (0)77 3897 206[cid:image766848.png@5BC17103.DADB3167]+31 (0)6 5337 2873[cid:image282789.png@4D1CE657.B6FB72BF]t.hendriks@frankort.nl<mailto:t.hendriks@frankort.nl>[cid:image490751.png@AE7A944C.6CA2F063]http://www.frankort.nl/[Facebook]<https://www.facebook.com/frankortenkoning>[LinkedIn]<https://www.linkedin.com/company/frankort-&-koning>[Twitter]<https://www.twitter.com/frankort_koning>[Frankort & Koning B.V.]<https://www.google.nl/maps/place/Frankort+en+Koning/@51.3977496,6.1474564,14z/data=!4m8!1m2!2m1!1sFrankort+%26+Koning+B.V.!3m4!1s0x47c744dd667d543d:0xc725d6533195f59b!8m2!3d51.4103672!4d6.1307674>​​Frankort & Koning is aware that fake email messages can be used in order to trick customers & suppliers into making payments to fraudulent bank accounts.​Frankort & Koning will NEVER ask you to change our bank account details by email only.​Should you receive an email from Frankort & Koning advising you of new bank account details please speak by phone to your regular contact in Frankort & Koning to confirm that the request is genuine.​Please remain vigilant of fraudulent activity.​General terms and conditions of delivery are applicable to our services. These conditions can be viewed on our website<https://frankort.nl/nl/leveringsvoorwaarden>.


