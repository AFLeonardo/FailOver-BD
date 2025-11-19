CREATE TABLE Clientes (
    id_cliente INT PRIMARY KEY AUTO_INCREMENT,
    nombre VARCHAR(50)
);

CREATE TABLE Pedidos (
    id_pedido INT PRIMARY KEY AUTO_INCREMENT,
    id_cliente INT,
    total DECIMAL(10,2),
    FOREIGN KEY (id_cliente) REFERENCES Clientes(id_cliente)
);

CREATE TABLE RegistroPedidos (
    id_registro INT PRIMARY KEY AUTO_INCREMENT,
    id_pedido INT,
    id_cliente INT,
    total DECIMAL(10,2),
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla para registrar failovers y backups
CREATE TABLE system_events (
    id INT PRIMARY KEY AUTO_INCREMENT,
    primary_node VARCHAR(50) NOT NULL,
    replica_node VARCHAR(50) NOT NULL,
    last_failover DATETIME,
    last_backup DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    event_type VARCHAR(20) NOT NULL DEFAULT 'FAILOVER'
);


INSERT INTO Clientes (nombre)
VALUES ('Leonardo'), ('Edna'), ('Carlos'), ('Sofía');

INSERT INTO Pedidos (id_cliente, total)
VALUES
(1, 1500.00),
(2, 800.00),
(3, 1200.00),
(4, 600.00);


/* -- Creamos la vista
CREATE VIEW vista_pedidos AS
SELECT 
    p.id_pedido AS 'ID Pedido',
    c.nombre AS 'Cliente',
    p.total AS 'Total del Pedido'
FROM 
    Pedidos p
INNER JOIN 
    Clientes c ON p.id_cliente = c.id_cliente;

-- Consultamos la vista
SELECT * FROM vista_pedidos; */

--Crear trigger
DELIMITER $$

CREATE TRIGGER insertar_pedido
AFTER INSERT ON Pedidos
FOR EACH ROW
BEGIN
    INSERT INTO RegistroPedidos (id_pedido, id_cliente, total)
    VALUES (NEW.id_pedido, NEW.id_cliente, NEW.total);
END $$

DELIMITER ;

INSERT INTO Pedidos (id_cliente, total)
VALUES (1, 2050.00);

SELECT * FROM RegistroPedidos;
SELECT * FROM Pedidos;