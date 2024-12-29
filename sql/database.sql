CREATE TABLE `closed_trades` (
  `trade_id` INT NOT NULL,
  `c_pair` CHAR(7) NOT NULL,
  `entry` DECIMAL(6,2) NOT NULL,
  `exit_price` DECIMAL(6,2) NOT NULL,
  `size` DECIMAL(10,2) NOT NULL,
  `trade_type` VARCHAR(5) NOT NULL,
  `trade_date` DATE NOT NULL,
  PRIMARY KEY (`trade_id`),
  CONSTRAINT `closed_trades_ibfk_1` FOREIGN KEY (`trade_id`) REFERENCES `trades` (`trade_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Create the `deleted_trades` table
CREATE TABLE `deleted_trades` (
  `trade_id` INT NOT NULL,
  `c_pair` CHAR(7) NOT NULL,
  `entry` DECIMAL(6,2) NOT NULL,
  `exit_price` DECIMAL(6,2) NOT NULL,
  `size` DECIMAL(10,2) NOT NULL,
  `trade_type` VARCHAR(5) NOT NULL,
  `trade_date` DATE NOT NULL,
  PRIMARY KEY (`trade_id`),
  CONSTRAINT `deleted_trades_ibfk_1` FOREIGN KEY (`trade_id`) REFERENCES `trades` (`trade_id`);

-- Create the `live_report` table
CREATE TABLE `live_report` (
  `rep_id` INT NOT NULL,
  `open_pl` DECIMAL(7,2) NOT NULL,
  `total_invested` DECIMAL(12,2) DEFAULT '0.00',
  PRIMARY KEY (`rep_id`),
  CONSTRAINT `live_report_ibfk_1` FOREIGN KEY (`rep_id`) REFERENCES `report` (`rep_id`));

-- Create the `open_trades` table
CREATE TABLE `open_trades` (
  `trade_id` INT NOT NULL,
  `c_pair` CHAR(7) NOT NULL,
  `entry` DECIMAL(6,2) NOT NULL,
  `size` DECIMAL(10,2) NOT NULL,
  `trade_type` VARCHAR(5) NOT NULL,
  PRIMARY KEY (`trade_id`),
  CONSTRAINT `open_trades_ibfk_1` FOREIGN KEY (`trade_id`) REFERENCES `trades` (`trade_id`));

-- Create the `regular_report` table
CREATE TABLE `regular_report` (
  `rep_id` INT NOT NULL,
  `net_pl` DECIMAL(10,2) NOT NULL,
  `total_trades` INT DEFAULT 0,
  PRIMARY KEY (`rep_id`),
  CONSTRAINT `regular_report_ibfk_1` FOREIGN KEY (`rep_id`) REFERENCES `report` (`rep_id`));

-- Create the `report` table
CREATE TABLE `report` (
  `rep_id` INT NOT NULL AUTO_INCREMENT,
  `generated_on` DATETIME NOT NULL,
  PRIMARY KEY (`rep_id`));