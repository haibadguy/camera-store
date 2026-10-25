package com.camerastore.modules.advisor;

import com.sun.net.httpserver.HttpServer;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.io.UncheckedIOException;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.concurrent.Executors;

/**
 * FastAPI giả lập cho test: một máy chủ HTTP thật (JDK HttpServer) trên cổng ngẫu nhiên. Mỗi đường dẫn + query
 * ("/recommend?user_id=409&k=10") trả một phản hồi cố định, thường là phản hồi thật của FastAPI đã lưu trong
 * src/test/resources/fastapi/. Ghi lại các yêu cầu nhận được để kiểm Spring gửi đúng tham số.
 */
class FakeModelService {
    record Reply(int status, String contentType, byte[] body, long delayMs) {}

    private final HttpServer server;
    private final Map<String, Reply> replies = new ConcurrentHashMap<>();
    final List<String> received = new CopyOnWriteArrayList<>();

    FakeModelService() {
        try {
            server = HttpServer.create(new InetSocketAddress("127.0.0.1", 0), 0);
        } catch (IOException e) {
            throw new UncheckedIOException(e);
        }
        server.setExecutor(Executors.newCachedThreadPool());   // yêu cầu chậm không chặn yêu cầu khác
        server.createContext("/", ex -> {
            String q = ex.getRequestURI().getRawQuery();
            String key = ex.getRequestURI().getPath() + (q == null ? "" : "?" + q);
            received.add(key);
            Reply r = replies.getOrDefault(key, new Reply(404, "application/json",
                    "{\"error\": {\"code\": \"NOT_FOUND\", \"message\": \"Not Found\", \"details\": {}}}"
                            .getBytes(StandardCharsets.UTF_8), 0));
            try {
                Thread.sleep(r.delayMs());
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
            try (OutputStream out = ex.getResponseBody()) {
                ex.getResponseHeaders().set("Content-Type", r.contentType());
                ex.sendResponseHeaders(r.status(), r.body().length);
                out.write(r.body());
            } catch (IOException ignored) {
                // Spring đã bỏ kết nối (hết giờ)
            }
        });
        server.start();
    }

    String baseUrl() {
        return "http://127.0.0.1:" + server.getAddress().getPort();
    }

    /** Trả nguyên file src/test/resources/fastapi/{file} với mã HTTP status. */
    void file(String key, int status, String file) {
        replies.put(key, new Reply(status, "application/json", fixture(file), 0));
    }

    void raw(String key, int status, String contentType, String body, long delayMs) {
        replies.put(key, new Reply(status, contentType, body.getBytes(StandardCharsets.UTF_8), delayMs));
    }

    static byte[] fixture(String file) {
        try (InputStream in = FakeModelService.class.getResourceAsStream("/fastapi/" + file)) {
            if (in == null) {
                throw new IllegalArgumentException("Không có fixture " + file);
            }
            return in.readAllBytes();
        } catch (IOException e) {
            throw new UncheckedIOException(e);
        }
    }
}
