<?php

$host = 'localhost';
$dbname = 'list_products';
$username = 'root';
$password = 'Relic11&';

$conn = new PDO("mysql:host=$host;dbname=$dbname", $username, $password);

$data = json_decode(file_get_contents('php://input'), true);

if($data){
    foreach($data as $item){
        $stmt = $conn->prepare("INSERT INTO cart (id, id_product, price) VALUES (:id, :id_product, :price)");
        $stmt->bindParam(':id', $item['id']);
        $stmt->bindParam(':id_product', $item['nombre']);
        $stmt->bindParam(':price', $item['precio']);
        $stmt->execute();
    }

    echo json_encode(['message' => 'Compra procesada exitosamente']);
} else{
    echo json_encode(['message'=> 'No se recibieron datos']);
}



?>