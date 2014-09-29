
curl http://127.0.0.1:5000/orders/import/ -d "data=id|name|email|state|zipcode|birthday\n53444|Stone Dominguez|ligula.Aliquam.erat@semperegestasurna.com|NY|40302|Feb 27, 1997" -X PUT

curl http://127.0.0.1:5000/orders/import/ -d "data=id|name|email|state|zipcode|birthday\n2444|Stone Dominguez|ligula.Aliquam.erat@semperegestasurna.com|NY|40302|Feb 27, 1963" -X PUT

curl http://127.0.0.1:5000/orders/import/ -d "data=id|name|email|state|zipcode|birthday\n2329|Mary Dominguez|ligula.Aliquam.erat@semperegestasurna.com|NJ|40302|Feb 27, 1963" -X PUT
