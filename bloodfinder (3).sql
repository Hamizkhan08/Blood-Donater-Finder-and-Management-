-- phpMyAdmin SQL Dump
-- version 5.2.1
-- Host: 127.0.0.1
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.0.30

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `bloodfinder`
--

-- --------------------------------------------------------

--
-- Table structure for table `admins`
--

CREATE TABLE IF NOT EXISTS `admins` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `username` varchar(100) NOT NULL,
  `password` varchar(200) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `admins`
--

INSERT INTO `admins` (`id`, `username`, `password`) VALUES
(1, 'admin', 'scrypt:32768:8:1$CMXAxOnQrwFJTdOZ$863117ea76d97a7e3c0bcd51610df2e29dca27931c7b38c4b324925707b94c9a4dec820ff1c5716a888f836a6e290d57e50706cad37279a9556a550819709571'),
(2, 'admin@admin', 'scrypt:32768:8:1$CMXAxOnQrwFJTdOZ$863117ea76d97a7e3c0bcd51610df2e29dca27931c7b38c4b324925707b94c9a4dec820ff1c5716a888f836a6e290d57e50706cad37279a9556a550819709571'),
(3, 'hamizkhan@ggsf.edu.in', 'scrypt:32768:8:1$XYlc2KBqmzzy9nck$0666cec657cf6d4e18295779b51e203eec8332b9e3f7c76fb1622aae02e26e5b14b8962f1b07e5162b83c321d25822b94fd14c98e7dcdcc4731f2bde1879821b');

-- --------------------------------------------------------

--
-- Table structure for table `blood_requests`
--

CREATE TABLE IF NOT EXISTS `blood_requests` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `requester_name` varchar(100) NOT NULL,
  `blood_group` varchar(10) NOT NULL,
  `location` varchar(100) NOT NULL,
  `contact` varchar(20) NOT NULL,
  `message` text DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `approved` tinyint(1) DEFAULT 0,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `blood_requests`
--

INSERT INTO `blood_requests` (`id`, `requester_name`, `blood_group`, `location`, `contact`, `message`, `created_at`, `approved`) VALUES
(1, 'Ramesh Shinde', 'O+', 'Nashik City Hospital, Nashik', '9876543210', 'Urgent O+ required for bypass surgery', '2026-09-01 10:15:00', 0),
(2, 'Sunita Patil', 'A+', 'Ruby Hall Clinic, Pune', '9823011223', 'Emergency ICU blood transfusion request', '2026-09-03 14:20:00', 0),
(3, 'Mohammad Ali', 'B+', 'Lilavati Hospital, Mumbai', '9819055443', 'Accident trauma recovery requirement', '2026-09-05 09:30:00', 1),
(4, 'Anita Sharma', 'O-', 'AIIMS, Delhi', '9910022334', 'Universal donor needed urgently for surgery', '2026-09-07 11:45:00', 1),
(5, 'Deepak Kumar', 'AB+', 'Apollo Hospital, Bangalore', '9740011223', 'Platelet & plasma transfusion request', '2026-09-09 16:00:00', 0);

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

CREATE TABLE IF NOT EXISTS `users` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `email` varchar(100) NOT NULL,
  `password` varchar(200) NOT NULL,
  `blood_group` varchar(10) NOT NULL,
  `location` varchar(100) NOT NULL,
  `contact` varchar(20) NOT NULL,
  `verified` tinyint(1) DEFAULT 0,
  PRIMARY KEY (`id`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `users`
--

INSERT INTO `users` (`id`, `name`, `email`, `password`, `blood_group`, `location`, `contact`, `verified`) VALUES
(1, 'Hamiz Khan', 'hamizkhan@ggsf.edu.in', 'scrypt:32768:8:1$XYlc2KBqmzzy9nck$0666cec657cf6d4e18295779b51e203eec8332b9e3f7c76fb1622aae02e26e5b14b8962f1b07e5162b83c321d25822b94fd14c98e7dcdcc4731f2bde1879821b', 'A+', 'Nashik', '9876501234', 1),
(2, 'Rajesh Sharma', 'rajesh.sharma@example.com', 'scrypt:32768:8:1$XYlc2KBqmzzy9nck$0666cec657cf6d4e18295779b51e203eec8332b9e3f7c76fb1622aae02e26e5b14b8962f1b07e5162b83c321d25822b94fd14c98e7dcdcc4731f2bde1879821b', 'O+', 'Mumbai', '9820012345', 1),
(3, 'Priya Patel', 'priya.patel@example.com', 'scrypt:32768:8:1$XYlc2KBqmzzy9nck$0666cec657cf6d4e18295779b51e203eec8332b9e3f7c76fb1622aae02e26e5b14b8962f1b07e5162b83c321d25822b94fd14c98e7dcdcc4731f2bde1879821b', 'B+', 'Pune', '9890023456', 1),
(4, 'Amit Verma', 'amit.verma@example.com', 'scrypt:32768:8:1$XYlc2KBqmzzy9nck$0666cec657cf6d4e18295779b51e203eec8332b9e3f7c76fb1622aae02e26e5b14b8962f1b07e5162b83c321d25822b94fd14c98e7dcdcc4731f2bde1879821b', 'A-', 'Delhi', '9811034567', 1),
(5, 'Sneha Reddy', 'sneha.reddy@example.com', 'scrypt:32768:8:1$XYlc2KBqmzzy9nck$0666cec657cf6d4e18295779b51e203eec8332b9e3f7c76fb1622aae02e26e5b14b8962f1b07e5162b83c321d25822b94fd14c98e7dcdcc4731f2bde1879821b', 'O-', 'Bangalore', '9845045678', 1),
(6, 'Vikram Singh', 'vikram.singh@example.com', 'scrypt:32768:8:1$XYlc2KBqmzzy9nck$0666cec657cf6d4e18295779b51e203eec8332b9e3f7c76fb1622aae02e26e5b14b8962f1b07e5162b83c321d25822b94fd14c98e7dcdcc4731f2bde1879821b', 'AB+', 'Hyderabad', '9849056789', 1),
(7, 'Ananya Sen', 'ananya.sen@example.com', 'scrypt:32768:8:1$XYlc2KBqmzzy9nck$0666cec657cf6d4e18295779b51e203eec8332b9e3f7c76fb1622aae02e26e5b14b8962f1b07e5162b83c321d25822b94fd14c98e7dcdcc4731f2bde1879821b', 'B-', 'Kolkata', '9830067890', 1),
(8, 'Karthik Nair', 'karthik.nair@example.com', 'scrypt:32768:8:1$XYlc2KBqmzzy9nck$0666cec657cf6d4e18295779b51e203eec8332b9e3f7c76fb1622aae02e26e5b14b8962f1b07e5162b83c321d25822b94fd14c98e7dcdcc4731f2bde1879821b', 'A+', 'Chennai', '9840078901', 1),
(9, 'Suresh Joshi', 'suresh.joshi@example.com', 'scrypt:32768:8:1$XYlc2KBqmzzy9nck$0666cec657cf6d4e18295779b51e203eec8332b9e3f7c76fb1622aae02e26e5b14b8962f1b07e5162b83c321d25822b94fd14c98e7dcdcc4731f2bde1879821b', 'O+', 'Nashik', '9822089012', 1),
(10, 'Meera Deshmukh', 'meera.d@example.com', 'scrypt:32768:8:1$XYlc2KBqmzzy9nck$0666cec657cf6d4e18295779b51e203eec8332b9e3f7c76fb1622aae02e26e5b14b8962f1b07e5162b83c321d25822b94fd14c98e7dcdcc4731f2bde1879821b', 'AB-', 'Pune', '9823090123', 1),
(11, 'Rohan Gupta', 'rohan.g@example.com', 'scrypt:32768:8:1$XYlc2KBqmzzy9nck$0666cec657cf6d4e18295779b51e203eec8332b9e3f7c76fb1622aae02e26e5b14b8962f1b07e5162b83c321d25822b94fd14c98e7dcdcc4731f2bde1879821b', 'B+', 'Mumbai', '9820091234', 1),
(12, 'Pooja Kapoor', 'pooja.k@example.com', 'scrypt:32768:8:1$XYlc2KBqmzzy9nck$0666cec657cf6d4e18295779b51e203eec8332b9e3f7c76fb1622aae02e26e5b14b8962f1b07e5162b83c321d25822b94fd14c98e7dcdcc4731f2bde1879821b', 'A+', 'Delhi', '9810092345', 1),
(13, 'Rahul Kumar', 'rahul.k@example.com', 'scrypt:32768:8:1$XYlc2KBqmzzy9nck$0666cec657cf6d4e18295779b51e203eec8332b9e3f7c76fb1622aae02e26e5b14b8962f1b07e5162b83c321d25822b94fd14c98e7dcdcc4731f2bde1879821b', 'O+', 'Bangalore', '9845093456', 1),
(14, 'Kavita Roy', 'kavita.r@example.com', 'scrypt:32768:8:1$XYlc2KBqmzzy9nck$0666cec657cf6d4e18295779b51e203eec8332b9e3f7c76fb1622aae02e26e5b14b8962f1b07e5162b83c321d25822b94fd14c98e7dcdcc4731f2bde1879821b', 'A-', 'Kolkata', '9830094567', 1),
(15, 'Manish Tiwari', 'manish.t@example.com', 'scrypt:32768:8:1$XYlc2KBqmzzy9nck$0666cec657cf6d4e18295779b51e203eec8332b9e3f7c76fb1622aae02e26e5b14b8962f1b07e5162b83c321d25822b94fd14c98e7dcdcc4731f2bde1879821b', 'B+', 'Nashik', '9822095678', 0),
(16, 'Divya Shah', 'divya.s@example.com', 'scrypt:32768:8:1$XYlc2KBqmzzy9nck$0666cec657cf6d4e18295779b51e203eec8332b9e3f7c76fb1622aae02e26e5b14b8962f1b07e5162b83c321d25822b94fd14c98e7dcdcc4731f2bde1879821b', 'O-', 'Mumbai', '9820096789', 0),
(17, 'Arjun Mehta', 'arjun.m@example.com', 'scrypt:32768:8:1$XYlc2KBqmzzy9nck$0666cec657cf6d4e18295779b51e203eec8332b9e3f7c76fb1622aae02e26e5b14b8962f1b07e5162b83c321d25822b94fd14c98e7dcdcc4731f2bde1879821b', 'AB+', 'Pune', '9890097890', 0);

COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
