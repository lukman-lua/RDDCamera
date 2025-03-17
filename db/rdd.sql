CREATE TABLE `Detections` (
  `id` integer PRIMARY KEY,
  `inspection_id` integer,
  `crack_type` varchar(255),
  `koordinat` varchar(255),
  `created_at` timestamp
);

CREATE TABLE `Inspections` (
  `id` integer PRIMARY KEY,
  `lokasi` varchar(255),
  `tanggal` datetime,
  `total_crack` integer,
  `count_longitudinal_cracks` integer,
  `count_transverse_cracks` integer,
  `count_alligator_cracks` integer,
  `count_potholes` integer,
  `created_at` timestamp
);

ALTER TABLE `Detections` ADD FOREIGN KEY (`inspection_id`) REFERENCES `Inspections` (`id`);
