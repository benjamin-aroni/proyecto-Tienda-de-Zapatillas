create database Web_python_Flask;
use Web_python_Flask;
 select*from dbo.zapatillas;

 CREATE TABLE dbo.zapatillas (
  id INT IDENTITY PRIMARY KEY,
  modelo NVARCHAR(100) NOT NULL,
  precio DECIMAL(10,2) NOT NULL,
  talla NVARCHAR(10) NOT NULL,
  imagen_url NVARCHAR(255) NULL
);
UPDATE dbo.zapatillas
SET imagen_url = '/static/imagenes/air_jordan_1_retro.jpeg'
WHERE modelo = 'Air Jordan 1 Retro';
