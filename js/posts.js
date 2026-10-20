/*
 * Índice de posts. Para publicar um novo:
 *   1. copia posts/_template.html para posts/NNN-slug.html e escreve o conteúdo
 *   2. adiciona uma entrada AQUI no topo da lista
 * É só isso. Sem CMS, sem build.
 */
const POSTS = [
  {
    id: "003",
    slug: "003-sniffer-de-lan-caseiro",
    title: "sniffer de lan caseiro",
    date: "2026-10-10",
    tags: ["rede", "python", "lab"],
    desc: "Capturar pacotes na minha própria rede para perceber quem anda a falar com quem. Só no meu lab, claro."
  },
  {
    id: "002",
    slug: "002-um-servidor-em-30-linhas",
    title: "um servidor http em 30 linhas",
    date: "2026-10-05",
    tags: ["http", "python", "minimal"],
    desc: "Sockets à moda antiga: aceitar uma ligação, ler o pedido, responder. Sem framework nenhum."
  },
  {
    id: "001",
    slug: "001-hello-world",
    title: "hello, world",
    date: "2026-10-01",
    tags: ["meta"],
    desc: "Porquê este site existe, como está montado e o que esperar daqui para a frente."
  }
];
