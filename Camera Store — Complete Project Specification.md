# Camera Store â€” Complete Project Specification

> **Document purpose:** This document is the single source of truth for the scope, architecture, technologies, database, modules, features, and implementation boundaries of the Camera Store project.
>
> AI coding assistants working on this repository MUST use this document as the primary project context and MUST NOT arbitrarily add features, tables, modules, technologies, or architectural patterns that are not defined here.

---

# 1. Project Overview

## 1.1 Project Name

**Camera Store**

## 1.2 Project Type

E-commerce website for selling cameras and photography equipment.

The system integrates a **Recommendation System** to recommend products based on product characteristics and user behavior.

## 1.3 Project Goal

The project aims to build a complete camera e-commerce platform with:

- Customer authentication.
- Product browsing and searching.
- Product filtering.
- Product detail pages.
- Shopping cart.
- Wishlist.
- Checkout.
- Order management.
- Product reviews.
- Inventory management.
- User behavior tracking.
- Recommendation System.
- Admin management.
- Basic business statistics.

The main academic highlight is the **Recommendation System**.

---

# 2. Project Constraints

| Item | Decision |
|---|---|
| Team size | 3 people |
| Duration | 8 weeks |
| Architecture | Monolithic |
| Frontend | React + Vite + TypeScript |
| Backend | Spring Boot + Java |
| ORM | JPA/Hibernate + Flyway |
| Database | PostgreSQL |
| AI / ML | Python |
| Recommendation | Content-Based first, Collaborative / Hybrid optional |
| Cache | Redis |
| Image storage | Cloudinary |
| Containerization | Docker Compose |
| Authentication | JWT |
| API style | REST API |

---

# 3. Architecture

## 3.1 Architectural Decision

The system uses a **Monolithic Architecture**.

The backend is one Spring Boot application.

The system is modular internally, but modules are not deployed as independent microservices.

There is:

- One backend application.
- One database.
- One main API.
- One frontend SPA.
- One AI/recommendation component integrated into the application workflow.

The project MUST NOT be converted into a microservices architecture.

---

# 4. High-Level Architecture

```text
                         â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
                         â”‚      Customer        â”‚
                         â”‚       Browser        â”‚
                         â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                                    â”‚
                                    â–¼
                         â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
                         â”‚   React + Vite SPA   â”‚
                         â”‚    TypeScript        â”‚
                         â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                                    â”‚ REST API
                                    â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚                    Spring Boot Monolithic Backend                â”‚
â”‚                                                             â”‚
â”‚  Auth        Users        Products       Categories         â”‚
â”‚  Brands      Cart         Wishlist       Orders             â”‚
â”‚  Reviews     Inventory    Payments       Coupons            â”‚
â”‚  Shipment    UserBehavior Recommendation Admin             â”‚
â”‚                                                             â”‚
â”‚                 Recommendation Module                       â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                           â”‚
              â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
              â–¼                         â–¼
       â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”          â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
       â”‚    JPA/Hibernate + Flyway    â”‚          â”‚    Redis     â”‚
       â”‚     ORM      â”‚          â”‚    Cache     â”‚
       â””â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”˜          â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
              â”‚
              â–¼
       â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
       â”‚    PostgreSQL     â”‚
       â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜


Recommendation training / experimentation:

Python
â”œâ”€â”€ pandas
â”œâ”€â”€ numpy
â””â”€â”€ scikit-learn
```

---

# 5. Technology Stack

## 5.1 Backend

```text
Spring Boot
TypeScript
JPA/Hibernate + Flyway
JWT
REST API
Swagger
Jakarta Bean Validation
Spring Security validation
```

## 5.2 Frontend

```text
React
Vite
TypeScript
React Router
```

Recommended:

```text
TanStack Query
```

for server-state/data fetching.

React Context should be limited to global client-side state such as authentication/session-level state.

---

# 6. Database

## 6.1 Database Technology

PostgreSQL.

JPA/Hibernate + Flyway is responsible for ORM and database access.

Main files:

```text
backend/src/main/resources/db/migration/
â””â”€â”€ V1__create_products.sql
```

---

# 7. Database Scope â€” 25 Tables

The project is designed around **25 database tables**.

The existence of a table does not mean that every advanced feature associated with that table must be fully implemented.

The tables are divided into implementation priorities.

---

## 7.1 Core Tables

These tables represent the main business flow and should be implemented to a high level of completeness.

### 1. User

Stores customer and administrator accounts.

Main responsibilities:

- Authentication.
- User profile.
- Role.
- Account status.
- Basic user information.

Roles:

```text
CUSTOMER
ADMIN
```

---

### 2. Address

Stores customer shipping addresses.

Relationship:

```text
User 1 â”€â”€â”€ N Address
```

---

### 3. Brand

Stores camera and equipment brands.

Examples:

```text
Canon
Sony
Nikon
Fujifilm
Panasonic
Olympus
```

---

### 4. Category

Stores product categories.

Examples:

```text
Mirrorless Camera
DSLR Camera
Compact Camera
Lens
Tripod
Memory Card
Battery
Camera Bag
```

---

### 5. Product

Stores the main product information.

Examples of attributes:

```text
name
description
brand
category
price
status
rating
specifications
```

---

### 6. ProductVariant

Stores product variations.

Examples:

```text
Body Only
Kit 15-45mm
Kit 18-55mm
Black
Silver
```

---

### 7. ProductImage

Stores product images.

Images should normally be stored using Cloudinary.

The database stores metadata and URLs rather than binary image data.

---

### 8. Cart

Stores a user's shopping cart.

Relationship:

```text
User 1 â”€â”€â”€ 1 Cart
```

---

### 9. CartItem

Stores products contained in a cart.

Relationship:

```text
Cart 1 â”€â”€â”€ N CartItem
```

---

### 10. Wishlist

Stores products saved by a customer.

Relationship:

```text
User 1 â”€â”€â”€ N Wishlist
Product 1 â”€â”€â”€ N Wishlist
```

---

### 11. Order

Stores customer orders.

Main responsibilities:

- Order creation.
- Order status.
- Total amount.
- Customer information.
- Checkout information.

Example statuses:

```text
PENDING
CONFIRMED
PROCESSING
SHIPPED
COMPLETED
CANCELLED
```

---

### 12. OrderItem

Stores individual products inside an order.

Relationship:

```text
Order 1 â”€â”€â”€ N OrderItem
Product 1 â”€â”€â”€ N OrderItem
```

---

### 13. Review

Stores customer product reviews and ratings.

Example:

```text
rating: 1â€“5
comment
user
product
```

---

### 14. UserBehavior

This table is important for the Recommendation System.

It records user interactions.

Supported behavior types include:

```text
VIEW
CLICK
SEARCH
ADD_TO_CART
WISHLIST
PURCHASE
REVIEW
```

The minimum required behavior tracking is:

```text
VIEW
ADD_TO_CART
PURCHASE
```

The additional events may be implemented if time permits.

---

### 15. Inventory

Stores current product stock information.

Responsibilities:

- Current stock.
- Reserved quantity if needed.
- Stock status.

The system must prevent orders from reducing stock below zero.

---

# 8. Supporting Tables

These tables support additional business functionality.

---

## 16. Payment

Stores payment information.

For the first implementation:

```text
FAKE_PAYMENT
```

is sufficient.

Real payment gateways such as VNPay/MoMo are optional.

---

## 17. Shipment

Stores basic shipping information.

The first implementation only needs basic shipping information.

A complex logistics system is NOT required.

---

## 18. Coupon

Stores discount codes.

Basic functionality:

```text
code
discount type
discount value
start date
end date
status
```

---

## 19. OrderCoupon

Associates coupons with orders.

This allows the system to record which coupon was applied to an order.

---

## 20. SystemLog

Stores important system/admin actions when required.

Examples:

```text
CREATE_PRODUCT
UPDATE_PRODUCT
DELETE_PRODUCT
UPDATE_ORDER_STATUS
LOGIN
```

A complex enterprise audit system is not required.

---

## 21. Notification

Stores basic user notifications.

Examples:

```text
Order confirmed
Order completed
Promotion
System message
```

Real-time notification is NOT required.

---

# 9. Advanced / Optional Tables

These tables are part of the planned 25-table design but are lower priority.

---

## 22. Bundle

Represents a product bundle/combo.

Example:

```text
Camera + Lens + Memory Card
```

Implementation is optional.

---

## 23. BundleItem

Stores products contained in a bundle.

Implementation is optional.

---

## 24. Analytics

Stores or supports aggregated business/recommendation analytics.

Possible metrics:

```text
Sales
Orders
Product views
Recommendation clicks
CTR
```

Advanced analytics is optional.

---

## 25. RecommendationMetric

Stores metrics used to evaluate the Recommendation System.

Possible metrics:

```text
Precision@K
Recall@K
CTR
Hit Rate
Response Time
```

The exact implementation depends on the available data.

---

# 10. Database Priority

## Core

```text
User
Address
Brand
Category
Product
ProductVariant
ProductImage
Cart
CartItem
Wishlist
Order
OrderItem
Review
UserBehavior
Inventory
```

These should be completed first.

---

## Important

```text
Payment
Shipment
Coupon
OrderCoupon
SystemLog
Notification
```

These should be implemented only after the core business flow works.

---

## Advanced

```text
Bundle
BundleItem
Analytics
RecommendationMetric
```

These can remain partially implemented if the project reaches the deadline.

---

# 11. Backend Modules

The Spring Boot backend is organized by domain.

```text
backend/src/modules/

auth/
users/
addresses/
brands/
categories/
products/
product-images/
product-variants/
carts/
wishlists/
orders/
order-items/
payments/
shipments/
coupons/
bundles/
reviews/
inventory/
user-behavior/
recommendations/
notifications/
analytics/
system-logs/
admin/
```

Not every module needs the same implementation depth.

---

# 12. Backend Common Infrastructure

```text
backend/src/

common/
â”œâ”€â”€ decorators/
â”œâ”€â”€ guards/
â”œâ”€â”€ filters/
â”œâ”€â”€ interceptors/
â”œâ”€â”€ middleware/
â”œâ”€â”€ pipes/
â”œâ”€â”€ exceptions/
â”œâ”€â”€ pagination/
â””â”€â”€ utils/

config/

database/

constants/

enums/
```

The project should avoid creating infrastructure solely for theoretical enterprise architecture.

Only infrastructure actually required by the application should be implemented.

---

# 13. Backend Module Structure

A typical module should follow:

```text
products/
â”œâ”€â”€ dto/
â”‚   â”œâ”€â”€ create-product.dto.ts
â”‚   â”œâ”€â”€ update-product.dto.ts
â”‚   â””â”€â”€ query-product.dto.ts
â”‚
â”œâ”€â”€ products.controller.ts
â”œâ”€â”€ products.service.ts
â”œâ”€â”€ products.module.ts
â””â”€â”€ products.spec.ts
```

A repository layer should only be introduced where it provides clear value.

Do NOT create unnecessary abstractions only to imitate enterprise architecture.

---

# 14. Authentication

Authentication uses:

```text
JWT
```

Required functionality:

- Register.
- Login.
- Get current user.
- Update profile.
- Password hashing.
- Role-based authorization.

Roles:

```text
CUSTOMER
ADMIN
```

Admin-only operations must be protected by authorization guards.

---

# 15. Product Management

Customers can:

- View products.
- Search products.
- Filter products.
- Sort products.
- View product details.
- View product images.
- View product variants.
- View reviews.

Admins can:

- Create product.
- Update product.
- Delete/deactivate product.
- Manage product images.
- Manage variants.
- Manage categories.
- Manage brands.
- Manage inventory.

---

# 16. Camera Product Domain

The product model should support camera-specific attributes where useful.

Examples:

```text
sensor type
sensor size
megapixels
mount
camera type
video resolution
iso range
weight
price range
brand
category
```

These attributes are important because they can be used as features by the Recommendation System.

The schema should not contain dozens of camera-specific columns unless they are actually required.

A flexible specification structure may be considered where appropriate.

---

# 17. Cart

Required functionality:

- Add product.
- Remove product.
- Update quantity.
- View cart.
- Clear cart.
- Validate stock before checkout.

---

# 18. Wishlist

Required functionality:

- Add product.
- Remove product.
- View wishlist.

---

# 19. Order

Required functionality:

```text
Cart
 â†“
Checkout
 â†“
Validate stock
 â†“
Create Order
 â†“
Create OrderItems
 â†“
Reduce inventory
 â†“
Clear Cart
```

Order creation must use a database transaction.

JPA/Hibernate + Flyway transaction should be used to keep the following operations consistent:

```text
Create Order
Create OrderItems
Update Inventory
Clear Cart
```

The system must avoid partial orders.

---

# 20. Payment

Initial implementation:

```text
Fake Payment
```

Example:

```text
CASH
FAKE_CARD
```

Real payment integration is optional.

The architecture should leave room for a future payment gateway without making payment integration a dependency of the core checkout flow.

---

# 21. Review

Customers can:

- Rate products.
- Write reviews.
- View reviews.

Basic validation should prevent inappropriate review behavior such as unlimited duplicate reviews for the same purchased product if the project rules require verified purchase reviews.

---

# 22. User Behavior Tracking

The Recommendation System requires behavioral data.

Minimum events:

```text
VIEW
ADD_TO_CART
PURCHASE
```

Additional events:

```text
CLICK
SEARCH
WISHLIST
REVIEW
```

Each behavior should contain enough information to identify:

```text
user
product
event type
timestamp
```

Anonymous behavior may be considered later, but it is not mandatory for the first version.

---

# 23. Recommendation System

The Recommendation System is the main academic component.

The project should be implemented progressively.

---

## 23.1 Phase 1 â€” Content-Based Recommendation

This is mandatory.

The system recommends products based on product similarity.

Possible product features:

```text
Brand
Category
Camera Type
Mount
Sensor
Megapixels
Price Range
Video Resolution
Other relevant specifications
```

The features are transformed into numerical vectors.

Similarity can be calculated using:

```text
Cosine Similarity
```

Example:

```text
Product A
      â†“
Feature Vector
      â†“
Cosine Similarity
      â†“
Similar Products
      â†“
Top-K Recommendations
```

---

# 24. Collaborative Filtering

Collaborative Filtering is optional / should-have.

It can use user behavior such as:

```text
VIEW
ADD_TO_CART
PURCHASE
```

Possible approach:

```text
User Ă— Product interaction matrix
```

or item-based collaborative filtering.

The implementation should remain simple enough for the project timeline.

---

# 25. Hybrid Recommendation

Hybrid recommendation is optional.

If implemented, use a simple weighted approach:

```text
Final Score
=
Î± Ă— Content Score
+
Î² Ă— Collaborative Score
```

Example:

```text
Î± = 0.7
Î² = 0.3
```

The exact weights should be experimentally evaluated rather than treated as universally correct.

---

# 26. Recommendation Module Structure

Recommended structure:

```text
recommendations/

â”œâ”€â”€ algorithms/
â”‚   â”œâ”€â”€ content-based/
â”‚   â”œâ”€â”€ collaborative/
â”‚   â””â”€â”€ hybrid/
â”‚
â”œâ”€â”€ services/
â”‚   â”œâ”€â”€ recommendation.service.ts
â”‚   â””â”€â”€ feature.service.ts
â”‚
â”œâ”€â”€ cache/
â”‚   â””â”€â”€ recommendation-cache.service.ts
â”‚
â”œâ”€â”€ evaluation/
â”‚   â””â”€â”€ recommendation-metrics.service.ts
â”‚
â”œâ”€â”€ dto/
â”œâ”€â”€ recommendations.controller.ts
â””â”€â”€ recommendations.module.ts
```

The algorithm implementation must remain understandable.

Do not over-engineer the Recommendation module.

---

# 27. Python AI Component

Python is used for Recommendation experimentation, training, evaluation, and data processing.

Possible libraries:

```text
Python
pandas
numpy
scikit-learn
```

The AI directory may be:

```text
ai/

â”œâ”€â”€ datasets/
â”œâ”€â”€ notebooks/
â”œâ”€â”€ training/
â”œâ”€â”€ inference/
â”œâ”€â”€ evaluation/
â”œâ”€â”€ models/
â”œâ”€â”€ scripts/
â””â”€â”€ requirements.txt
```

Python should NOT become a second full backend application.

The project remains a Monolithic Web Application.

---

# 28. Recommendation Integration

The preferred approach is to keep the web application architecture simple.

The Recommendation System may be:

1. Trained/offline using Python.
2. Saved as a model or generated recommendation data.
3. Loaded/used by the Spring Boot Recommendation Module where practical.

If direct Python execution is required during development, it should remain an implementation detail rather than becoming a separate microservice.

The project must NOT introduce a Python REST microservice unless the team explicitly decides to change the architecture.

---

# 29. Recommendation Cold Start

The system should handle users with insufficient behavior data.

For a new user:

```text
User has no history
        â†“
Content-Based / Popular Products
        â†“
Recommendation
```

For an existing user:

```text
User behavior
        â†“
Personalized recommendation
```

This is important because a new e-commerce system will initially have very little collaborative data.

---

# 30. Recommendation Cache

Redis may be used to cache recommendation results.

Example:

```text
recommendation:user:{userId}
```

Cache should preferably contain product IDs or compact recommendation results rather than unnecessarily large product objects.

Cache expiration should be configurable.

---

# 31. Recommendation Evaluation

The Recommendation System should not only demonstrate that recommendations exist.

The project should attempt to evaluate recommendation quality.

Possible metrics:

```text
Precision@K
Recall@K
Hit Rate
CTR
Response Time
```

For the actual project, only metrics supported by the available dataset should be reported.

CTR can be calculated from:

```text
Recommendation impression
+
Recommendation click
```

---

# 32. Redis

Redis is optional infrastructure but recommended.

Primary purpose:

```text
Recommendation caching
```

Possible future use:

```text
Session-related caching
Rate limiting
Temporary data
```

Do not introduce Redis for every possible use case.

---

# 33. Image Management

Cloudinary is the preferred image storage solution.

Database:

```text
stores image URL + metadata
```

Cloudinary:

```text
stores actual image
```

The backend must not store large binary image files directly in PostgreSQL.

---

# 34. Admin

The project requires an Admin interface.

Admin functionality:

```text
Dashboard
Products
Categories
Brands
Variants
Orders
Users
Inventory
Reviews
Coupons
```

Advanced analytics is optional.

---

# 35. Dashboard

The dashboard should provide basic statistics where practical.

Examples:

```text
Total users
Total products
Total orders
Total revenue
Best-selling products
Recent orders
```

Recommendation analytics are optional.

---

# 36. Frontend

Frontend technology:

```text
React
Vite
TypeScript
React Router
```

Recommended:

```text
TanStack Query
```

---

# 37. Frontend Pages

## Customer Pages

```text
Home
Products
Product Detail
Search
Cart
Wishlist
Checkout
Order History
Order Detail
Login
Register
Profile
```

---

## Admin Pages

```text
Admin Dashboard
Products
Product Create
Product Edit
Categories
Brands
Orders
Order Detail
Users
Inventory
Reviews
Coupons
```

Advanced analytics pages are optional.

---

# 38. Frontend Components

Common components:

```text
Navbar
Footer
Sidebar
SearchBar
ProductCard
ProductGrid
ProductFilter
ProductSort
Pagination
ReviewCard
Rating
CartItem
OrderSummary
CheckoutForm
Modal
Toast
Loading
EmptyState
ErrorState
```

Recommendation components:

```text
RecommendedProducts
SimilarProducts
PersonalizedProducts
```

---

# 39. Frontend State Management

Do not introduce Redux unless the project actually requires it.

Preferred approach:

```text
React Context
```

for:

```text
Authentication
```

and

```text
TanStack Query
```

for:

```text
Products
Cart
Orders
Reviews
Recommendations
```

The exact choice may be adjusted during implementation if necessary.

---

# 40. API

The backend exposes REST APIs.

Examples:

```text
POST   /api/auth/register
POST   /api/auth/login
GET    /api/users/me

GET    /api/products
GET    /api/products/:id
POST   /api/products
PATCH  /api/products/:id
DELETE /api/products/:id

GET    /api/categories
GET    /api/brands

GET    /api/cart
POST   /api/cart/items
PATCH  /api/cart/items/:id
DELETE /api/cart/items/:id

GET    /api/wishlist
POST   /api/wishlist
DELETE /api/wishlist/:productId

POST   /api/orders
GET    /api/orders
GET    /api/orders/:id

POST   /api/reviews
GET    /api/products/:id/reviews

GET    /api/recommendations/home
GET    /api/recommendations/product/:id
GET    /api/recommendations/user
```

Exact endpoint naming may be refined during API design but should remain RESTful and consistent.

---

# 41. API Documentation

Swagger should be used for API documentation.

The project should maintain:

```text
docs/API/
```

Possible files:

```text
openapi.json
API.md
```

Frontend developers should use the API specification rather than guessing request/response structures.

---

# 42. Validation and Security

Backend must include:

```text
DTO validation
JWT authentication
Role-based authorization
Password hashing
Input sanitization
CORS configuration
Environment variables
```

Sensitive information must never be committed to Git.

Examples:

```text
DATABASE_URL
JWT_SECRET
CLOUDINARY_API_KEY
CLOUDINARY_API_SECRET
```

---

# 43. Environment Configuration

Required files:

```text
.env.example
```

Actual:

```text
.env
```

must NOT be committed.

Example configuration:

```text
DATABASE_URL=
JWT_SECRET=

REDIS_URL=

CLOUDINARY_CLOUD_NAME=
CLOUDINARY_API_KEY=
CLOUDINARY_API_SECRET=
```

---

# 44. Docker

Docker Compose is used to make development environments consistent.

Expected services:

```text
postgresql
redis
backend
frontend
```

Additional services may be added only when required.

---

# 45. Development Environment

Required local tools:

```text
Node.js
npm
Python
PostgreSQL / Docker
Redis / Docker
Git
VS Code
```

Recommended:

```text
Docker Desktop
Postman
Swagger
JPA/Hibernate + Flyway Studio
```

---

# 46. Repository Structure

Recommended final structure:

```text
camera-store/
â”‚
â”œâ”€â”€ backend/
â”‚   â”œâ”€â”€ src/
â”‚   â”‚   â”œâ”€â”€ common/
â”‚   â”‚   â”œâ”€â”€ config/
â”‚   â”‚   â”œâ”€â”€ database/
â”‚   â”‚   â”œâ”€â”€ modules/
â”‚   â”‚   â””â”€â”€ main.ts
â”‚   â”‚
â”‚   â”œâ”€â”€ src/main/resources/db/migration/
â”‚   â”‚   â””â”€â”€ V1__create_products.sql
â”‚   â”‚
â”‚   â”œâ”€â”€ src/test/
â”‚   â”œâ”€â”€ pom.xml
â”‚   â””â”€â”€ .env.example
â”‚
â”œâ”€â”€ frontend/
â”‚   â”œâ”€â”€ src/
â”‚   â”‚   â”œâ”€â”€ api/
â”‚   â”‚   â”œâ”€â”€ components/
â”‚   â”‚   â”œâ”€â”€ hooks/
â”‚   â”‚   â”œâ”€â”€ layouts/
â”‚   â”‚   â”œâ”€â”€ pages/
â”‚   â”‚   â”œâ”€â”€ routes/
â”‚   â”‚   â”œâ”€â”€ services/
â”‚   â”‚   â”œâ”€â”€ types/
â”‚   â”‚   â”œâ”€â”€ utils/
â”‚   â”‚   â”œâ”€â”€ App.tsx
â”‚   â”‚   â””â”€â”€ main.tsx
â”‚   â”‚
â”‚   â”œâ”€â”€ public/
â”‚   â”œâ”€â”€ package.json
â”‚   â””â”€â”€ .env.example
â”‚
â”œâ”€â”€ ai/
â”‚   â”œâ”€â”€ datasets/
â”‚   â”œâ”€â”€ notebooks/
â”‚   â”œâ”€â”€ training/
â”‚   â”œâ”€â”€ inference/
â”‚   â”œâ”€â”€ evaluation/
â”‚   â”œâ”€â”€ models/
â”‚   â”œâ”€â”€ scripts/
â”‚   â”œâ”€â”€ requirements.txt
â”‚   â””â”€â”€ README.md
â”‚
â”œâ”€â”€ docs/
â”‚   â”œâ”€â”€ SRS/
â”‚   â”œâ”€â”€ ERD/
â”‚   â”œâ”€â”€ UML/
â”‚   â”œâ”€â”€ API/
â”‚   â”œâ”€â”€ Architecture/
â”‚   â”œâ”€â”€ AI/
â”‚   â”œâ”€â”€ Testing/
â”‚   â”œâ”€â”€ Report/
â”‚   â”œâ”€â”€ Presentation/
â”‚   â””â”€â”€ Meeting/
â”‚
â”œâ”€â”€ assets/
â”‚   â”œâ”€â”€ logo/
â”‚   â”œâ”€â”€ banners/
â”‚   â”œâ”€â”€ screenshots/
â”‚   â””â”€â”€ mockups/
â”‚
â”œâ”€â”€ scripts/
â”‚
â”œâ”€â”€ docker-compose.yml
â”œâ”€â”€ .env.example
â”œâ”€â”€ .gitignore
â”œâ”€â”€ README.md
â””â”€â”€ LICENSE
```

---

# 47. Development Priority

The project MUST follow this priority.

## Priority 1 â€” Core

```text
Authentication
Users
Brands
Categories
Products
Variants
Images
Cart
Wishlist
Orders
Inventory
Reviews
User Behavior
Content-Based Recommendation
Admin
```

These are the most important components.

---

## Priority 2 â€” Supporting

```text
Payment
Shipment
Coupon
OrderCoupon
SystemLog
Notification
Redis Cache
```

Implement after Priority 1 works.

---

## Priority 3 â€” Advanced

```text
Collaborative Filtering
Hybrid Recommendation
Bundle
BundleItem
Analytics
RecommendationMetric
```

These must NOT delay completion of the core system.

---

# 48. 8-Week Development Plan

## Week 1

```text
Project setup
Requirement confirmation
ERD
Database schema
JPA/Hibernate + Flyway schema
Migration
Seed
Docker
```

Deliverable:

```text
Database running
Seed data available
```

---

## Week 2

```text
Authentication
User
Address
Image upload
```

Deliverable:

```text
Register
Login
Profile
```

---

## Week 3

```text
Product
Category
Brand
Variant
Product Image
```

Deliverable:

```text
Product CRUD
Product listing
Product detail
Search
Filter
```

---

## Week 4

```text
Cart
Wishlist
Review
```

Deliverable:

```text
Customer shopping flow
```

---

## Week 5

```text
Order
OrderItem
Inventory
Payment
Shipment
```

Deliverable:

```text
Checkout
Order creation
Inventory update
Fake payment
```

---

## Week 6

```text
UserBehavior
Recommendation
Content-Based algorithm
```

Deliverable:

```text
Working Recommendation System
```

This is a critical milestone.

---

## Week 7

```text
Admin
Dashboard
Coupon
Redis
SystemLog
```

If the core is already stable:

```text
Collaborative Filtering
```

may be attempted.

---

## Week 8

```text
Bug fixing
Testing
Deployment
Documentation
Report
Slides
Demo
```

No major new feature should be started unless absolutely necessary.

---

# 49. Scope Control Rules

The project MUST follow these rules.

## Rule 1

Do not add a new database table without reviewing its business purpose.

## Rule 2

Do not add a new module only because it is common in enterprise applications.

## Rule 3

Do not convert the project into microservices.

## Rule 4

Do not introduce additional programming languages without a strong reason.

## Rule 5

Do not implement advanced AI before Content-Based Recommendation is working.

## Rule 6

Do not sacrifice core functionality for optional features.

## Rule 7

Do not let AI coding assistants redesign the architecture automatically.

## Rule 8

Database changes must be reviewed before migration.

## Rule 9

API contracts must be stable before frontend integration.

## Rule 10

The final week is primarily for testing, documentation, deployment, and presentation.

---

# 50. Database Freeze

At the end of Week 1:

```text
ERD
Flyway SQL migrations
database relationships
```

should be considered frozen.

Changes after this point require team review.

---

# 51. Feature Freeze

At the end of Week 7:

No major new functionality should be added.

The team should focus on:

```text
Bug fixing
Testing
UI improvement
Performance
Documentation
```

---

# 52. Code Freeze

At the beginning of Week 8:

The codebase should be considered feature-complete.

Only:

```text
Bug fixes
Security fixes
Performance fixes
UI fixes
Deployment fixes
```

should be performed.

---

# 53. Testing

Testing should cover at least:

## Authentication

```text
Register
Login
Invalid credentials
Unauthorized access
Role authorization
```

## Product

```text
Create
Read
Update
Delete
Search
Filter
Pagination
```

## Cart

```text
Add
Update
Remove
Stock validation
```

## Order

```text
Checkout
Transaction
Inventory reduction
Invalid stock
Order status
```

## Recommendation

```text
New user
Existing user
Similar products
No recommendation data
Top-K recommendation
```

---

# 54. Transaction Requirements

Order creation is a critical transaction.

The backend must ensure that:

```text
Order creation
+
Order item creation
+
Inventory update
+
Cart cleanup
```

are handled consistently.

If one critical operation fails, the transaction should roll back.

---

# 55. Git Workflow

Recommended branches:

```text
main
develop
```

Feature branches:

```text
feature/auth
feature/products
feature/cart
feature/orders
feature/recommendation
feature/admin
```

Do not commit directly to `main` during normal development.

---

# 56. Commit Convention

Recommended:

```text
feat: add product module
feat: implement cart API
fix: prevent negative inventory
fix: validate order stock
refactor: improve recommendation service
docs: update ERD
test: add order transaction tests
```

---

# 57. AI Coding Assistant Rules

AI coding assistants may help with:

```text
Boilerplate
DTOs
Controllers
Services
CRUD
Tests
Documentation
Refactoring
```

But AI MUST NOT independently:

```text
Change database architecture
Add tables
Remove tables
Change framework
Change architecture
Add microservices
Replace JPA/Hibernate + Flyway
Replace PostgreSQL
Change recommendation methodology
```

without explicit human approval.

---

# 58. Recommendation AI Rules

The Recommendation System is academically important.

Before generating recommendation code, the team should understand:

```text
Feature extraction
Vectorization
Similarity
Cosine similarity
Top-K selection
Cold start
Evaluation
```

The team must be able to explain the algorithm without relying on AI-generated explanations.

---

# 59. Definition of Done

A feature is considered complete only when:

```text
Database
+
Backend API
+
Validation
+
Frontend integration
+
Error handling
+
Basic testing
```

are completed as appropriate for that feature.

A module containing only generated boilerplate is NOT considered complete.

---

# 60. Minimum Viable Final Product

If time becomes limited, the final product MUST prioritize:

```text
1. Authentication
2. Product catalog
3. Product detail
4. Search/filter
5. Cart
6. Wishlist
7. Checkout
8. Order management
9. Inventory
10. Reviews
11. User behavior tracking
12. Content-Based Recommendation
13. Admin management
```

Optional features may be removed without compromising the core project.

---

# 61. Final Academic Highlight

The project should be presented not simply as:

> "A camera e-commerce website."

It should be presented as:

> **"A camera e-commerce platform integrated with a personalized Recommendation System based on product characteristics and user behavior."**

The main academic contribution is:

```text
E-commerce Data
      â†“
User Behavior
      â†“
Feature Engineering
      â†“
Recommendation Algorithm
      â†“
Product Similarity
      â†“
Top-K Recommendation
      â†“
User Interaction
      â†“
Evaluation
```

---

# 62. Final Scope Statement

The Camera Store project is a **Monolithic camera e-commerce platform** built with:

```text
React + Vite + TypeScript
            +
Spring Boot + JPA/Hibernate + Flyway
            +
PostgreSQL
            +
Redis
            +
Python / scikit-learn
```

The system contains a planned **25-table relational database**, modular backend architecture, SPA frontend, customer shopping workflow, administrator management, inventory, reviews, behavioral tracking, and Recommendation System.

The project prioritizes:

1. A complete and stable e-commerce core.
2. A working Content-Based Recommendation System.
3. Clear architecture.
4. Proper database design.
5. REST API design.
6. Testing.
7. Documentation.
8. Demonstrable academic value.

Advanced features such as Collaborative Filtering, Hybrid Recommendation, Bundles, advanced Analytics, real Payment Gateway integration, and advanced Notifications are secondary and MUST NOT jeopardize completion of the core system.

---

# 63. One-Sentence Project Definition

> **Camera Store is a monolithic camera e-commerce platform built with React, Spring Boot, JPA/Hibernate + Flyway, and PostgreSQL, enhanced with a Python-based Recommendation System that uses product features and user behavior to provide personalized product recommendations.**
