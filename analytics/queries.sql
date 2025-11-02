--Which doctor has the most confirmed appointments?

select 
    dc.doctor_id,
    dc.doctor_name, 
    count(ap.appointment_id) as number_of_confirmed_appointments
from healthtech.appointments ap
join healthtech.doctors dc
    on ap.doctor_id = dc.doctor_id
where ap.status = 'confirmed'
group by dc.doctor_id, dc.doctor_name
order by number_of_confirmed_appointments desc
limit 1;


--How many confirmed appointments does the patient with patient_id '34' have?
select 
ap.patient_id, 
count(ap.appointment_id) as number_of_confirmed_appoiments
from healthtech.appointments ap
left join healthtech.doctors dc
on ap.doctor_id = dc.doctor_id
where ap.status = 'confirmed' and ap.patient_id = 34
group by 1
order by number_of_confirmed_appoiments desc

--How many cancelled appointments are there between October 21, 2025, and October 24, 2025 (inclusive)?

select 
appointment_date,
count(ap.appointment_id) as number_of_confirmed_appoiments
from healthtech.appointments ap
left join healthtech.doctors dc
on ap.doctor_id = dc.doctor_id
where ap.status = 'cancelled' and appointment_date between '2025-10-21' and '2025-10-24' 
group by 1
order by appointment_date asc

--What is the total number of confirmed appointments for each doctor?

select 
dc.doctor_name, 
count(ap.appointment_id) as  number_of_confirmed_appoiments
from healthtech.appointments ap
left join healthtech.doctors dc
on ap.doctor_id = dc.doctor_id
where ap.status = 'confirmed'
group by 1
order by number_of_confirmed_appoiments desc