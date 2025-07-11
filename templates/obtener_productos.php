<?php
header('Content-Type: application/json');

$host = 'localhost';
$dbname = 'list_products';
$username = 'root';
$password = 'Relic11&';

try {
    $conn = new PDO("mysql:host=$host;dbname=$dbname", $username, $password);
    $conn->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION); //para detectar posibles errores en la baseDatos

    $stmt = $conn->query("SELECT id, product, price FROM products");
    $productos = $stmt->fetchAll(PDO::FETCH_ASSOC);

    echo json_encode($productos);
} catch (PDOException $e) {  //captura error PDO
    echo json_encode(['error' => $e->getMessage()]);
}
?>
