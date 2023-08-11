const express = require('express')
const app = express()
const port = 3000

app.get('/', (req, res) => {
  res.set('Cache-control', 'public, max-age=30')
  res.set('Age', '15')
  res.send(`
    <html>
      <body>Hello World!</body>
    </html>
  `)
})

app.listen(port, () => {
  console.log(`Example app listening on port ${port}`)
})