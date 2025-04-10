# kitchensink MongoDB Migration Plan

## 1. Current Application Overview

The analyzed application is a Java EE web application that utilizes various technologies including JSF, CDI, EJB, JPA, and Bean Validation. It is designed to manage member registrations and interactions with a database, likely using an H2 in-memory database for development and testing, with potential for PostgreSQL in production. The application is structured around a traditional Java EE architecture, with a focus on dependency injection and managed beans.

### 1.1 Key components of the current architecture:
- **Entity Model**:
  - `Member`: Represents a member in the system, containing fields for ID, name, email, and phone number.


- **Repositories**
  - MemberRepository: Interface for data access operations related to Member entities.


- **Database Configuration**
  - Datasource JNDI Name: java:jboss/datasources/KitchensinkQuickstartDS

  - Connection URL: jdbc:h2:mem:kitchensink-quickstart;DB_CLOSE_ON_EXIT=FALSE;DB_CLOSE_DELAY=-1

  - Driver: h2

  - Username: sa

  - Password: sa


### 1.2 API Definitions:
#### Member Registration
- **Path:** `/rest/members`
- **Summary:** Endpoint for registering a new member.

#### Get All Members
- **Path:** `/rest/members`
- **Summary:** Endpoint for retrieving a list of all members.

#### Get Member by ID
- **Path:** `/rest/members/{id}`
- **Summary:** Endpoint for retrieving a specific member by their ID.


### 1.3 Database Schemas
#### Member
`CREATE TABLE Member (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(25) NOT NULL CHECK (name NOT LIKE '%[^0-9]%'),
  email VARCHAR(255) NOT NULL UNIQUE,
  phone_number VARCHAR(12) NOT NULL CHECK (LENGTH(phone_number) BETWEEN 10 AND 12)
);`


## 2. MongoDB Migration Strategy

### 2.1 Schema Design
When migrating from a relational database to MongoDB, we need to rethink our data model. MongoDB's document model allows for embedded documents and references between documents.

#### Proposed MongoDB Schemas:
**Collection Name: `members`**
```
{
  _id: ObjectId,
  name: {
    type: String,
    required: true,
    validate: {
      validator: function(v) {
        return !/
        [0-9]/.test(v);
      },
      message: 'Name must not contain numbers!'
    },
    maxlength: 25
  },
  email: {
    type: String,
    required: true,
    unique: true
  },
  phone_number: {
    type: String,
    required: true,
    validate: {
      validator: function(v) {
        return v.length >= 10 && v.length <= 12;
      },
      message: 'Phone number must be between 10 and 12 digits!'
    }
  }
}
```

**Design Decisions:**

1. **Embedding vs Referencing**
    - The Member entity is self-contained and does not reference other entities, making it suitable for embedding.

    - Embedding allows for faster read operations since all member data is stored in a single document.

2. **Indexing Strategy**
    - The email field is marked as unique, which will require a unique index in MongoDB to enforce this constraint.

    - Indexing the email field will improve query performance when searching for members by email.

3. **Validation and Constraints**
    - MongoDB's schema-less nature allows for flexible data storage, but validation is implemented using Mongoose or similar libraries to enforce constraints.

    - Custom validation functions ensure that the name does not contain numbers and that the phone number length is appropriate.


### 2.2 Files to Change
#### CONFIGURATION

File: `input\kitchensink\src\main\webapp\WEB-INF\faces-config.xml`
```java
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.EnableWebMvc;
import org.springframework.web.servlet.config.annotation.ViewResolvers;
import org.springframework.web.servlet.config.annotation.ResourceHandlers;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

@Configuration
@EnableWebMvc
public class WebConfig implements WebMvcConfigurer {

    @Override
    public void addViewResolvers(ViewResolvers registry) {
        // Configure view resolvers here
    }

    @Override
    public void addResourceHandlers(ResourceHandlers registry) {
        // Configure resource handlers here
    }

    // Define navigation rules and other configurations as needed
}
```

File: `input\kitchensink\src\main\webapp\WEB-INF\beans.xml`
```java
import org.springframework.context.annotation.ComponentScan;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.mongodb.config.EnableMongoAuditing;

@Configuration
@ComponentScan(basePackages = "com.example")
@EnableMongoAuditing
public class AppConfig {

}
```

File: `input\kitchensink\src\main\java\org\jboss\as\quickstarts\kitchensink\rest\JaxRsActivator.java`
```java
package org.example.kitchensink.rest;

import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.EnableWebMvc;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@Configuration
@EnableWebMvc
@RestController
@RequestMapping("/rest")
public class RestActivator implements WebMvcConfigurer {
    // class body intentionally left blank
}
```

File: `input\kitchensink\src\main\resources\META-INF\persistence.xml`
```java
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.mongodb.config.AbstractMongoClientConfiguration;
import org.springframework.data.mongodb.repository.config.EnableMongoRepositories;
import com.mongodb.client.MongoClients;
import org.springframework.data.mongodb.core.MongoTemplate;
import org.springframework.beans.factory.annotation.Value;

@Configuration
@EnableMongoRepositories(basePackages = "com.example.repository")
public class MongoConfig extends AbstractMongoClientConfiguration {

    @Value("${spring.data.mongodb.uri}")
    private String mongoUri;

    @Override
    protected String getDatabaseName() {
        return "yourDatabaseName"; // Replace with your database name
    }

    @Bean
    @Override
    public MongoTemplate mongoTemplate() throws Exception {
        return new MongoTemplate(MongoClients.create(mongoUri), getDatabaseName());
    }
}
```

File: `input\kitchensink\src\main\webapp\WEB-INF\kitchensink-quickstart-ds.xml`
```java
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.data.mongodb.repository.MongoRepository;
import org.springframework.data.mongodb.config.AbstractMongoClientConfiguration;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.mongodb.core.MongoTemplate;
import com.mongodb.client.MongoClients;
import com.mongodb.client.MongoClient;

@SpringBootApplication
public class KitchensinkQuickstartApplication {
    public static void main(String[] args) {
        SpringApplication.run(KitchensinkQuickstartApplication.class, args);
    }
}

@Configuration
class MongoConfig extends AbstractMongoClientConfiguration {
    @Override
    protected String getDatabaseName() {
        return "kitchensink-quickstart";
    }

    @Bean
    public MongoClient mongoClient() {
        return MongoClients.create("mongodb://localhost:27017");
    }

    @Bean
    public MongoTemplate mongoTemplate() throws Exception {
        return new MongoTemplate(mongoClient(), getDatabaseName());
    }
}

interface KitchenSinkRepository extends MongoRepository<KitchenSinkEntity, String> {
    // Custom query methods can be defined here
}

class KitchenSinkEntity {
    // Define fields, getters, setters, and annotations for MongoDB
}
```

File: `input\kitchensink\src\main\java\org\jboss\as\quickstarts\kitchensink\util\Resources.java`
```java
package org.example.kitchensink.util;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.mongodb.core.MongoTemplate;
import org.springframework.data.mongodb.core.SimpleMongoClientDbFactory;
import org.springframework.beans.factory.annotation.Autowired;
import com.mongodb.client.MongoClients;

@Configuration
public class Resources {

    @Autowired
    private MongoTemplate mongoTemplate;

    @Bean
    public MongoTemplate mongoTemplate() {
        return new MongoTemplate(new SimpleMongoClientDbFactory(MongoClients.create("mongodb://localhost:27017/kitchensink"), "kitchensink"));
    }

    @Bean
    public Logger produceLog() {
        return LoggerFactory.getLogger(Resources.class);
    }
}
```

File: `input\kitchensink\src\test\resources\arquillian.xml`
```java
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.mongodb.config.AbstractMongoClientConfiguration;
import org.springframework.data.mongodb.core.MongoTemplate;
import com.mongodb.client.MongoClients;
import com.mongodb.client.MongoClient;

@SpringBootApplication
public class Application {
    public static void main(String[] args) {
        SpringApplication.run(Application.class, args);
    }
}

@Configuration
class MongoConfig extends AbstractMongoClientConfiguration {
    @Override
    protected String getDatabaseName() {
        return "your_database_name";
    }

    @Bean
    public MongoClient mongoClient() {
        return MongoClients.create("mongodb://localhost:27017");
    }

    @Bean
    public MongoTemplate mongoTemplate() {
        return new MongoTemplate(mongoClient(), getDatabaseName());
    }
}
```

File: `input\kitchensink\src\test\resources\META-INF\test-persistence.xml`
```java
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.data.mongodb.config.EnableMongoAuditing;
import org.springframework.data.mongodb.repository.config.EnableMongoRepositories;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.mongodb.core.MongoTemplate;
import com.mongodb.client.MongoClients;
import com.mongodb.client.MongoClient;

@SpringBootApplication
@EnableMongoRepositories
@EnableMongoAuditing
public class Application {

    public static void main(String[] args) {
        SpringApplication.run(Application.class, args);
    }

    @Bean
    public MongoClient mongoClient() {
        return MongoClients.create("mongodb://localhost:27017");
    }

    @Bean
    public MongoTemplate mongoTemplate() {
        return new MongoTemplate(mongoClient(), "your_database_name");
    }
}
```

#### TEST

File: `input\kitchensink\src\test\java\org\jboss\as\quickstarts\kitchensink\test\RemoteMemberRegistrationIT.java`
```java
package com.example.kitchensink.test;

import com.example.kitchensink.model.Member;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.ResponseEntity;
import org.springframework.http.MediaType;
import static org.junit.jupiter.api.Assertions.assertEquals;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
public class RemoteMemberRegistrationIT {

    @Autowired
    private TestRestTemplate restTemplate;

    @Test
    public void testRegister() {
        Member newMember = new Member();
        newMember.setName("Jane Doe");
        newMember.setEmail("jane@mailinator.com");
        newMember.setPhoneNumber("2125551234");

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        HttpEntity<Member> requestEntity = new HttpEntity<>(newMember, headers);

        ResponseEntity<String> response = restTemplate.exchange("/rest/members", HttpMethod.POST, requestEntity, String.class);

        assertEquals(200, response.getStatusCodeValue());
        assertEquals("", response.getBody());
    }
}
```

File: `input\kitchensink\src\test\java\org\jboss\as\quickstarts\kitchensink\test\MemberRegistrationIT.java`
```java
package com.example.kitchensink.test;

import static org.junit.jupiter.api.Assertions.assertNotNull;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.data.mongo.DataMongoTest;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.junit.jupiter.SpringExtension;
import com.example.kitchensink.model.Member;
import com.example.kitchensink.service.MemberRegistration;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

@ExtendWith(SpringExtension.class)
@DataMongoTest
@SpringBootTest
public class MemberRegistrationIT {
    private static final Logger log = LoggerFactory.getLogger(MemberRegistrationIT.class);

    @Autowired
    private MemberRegistration memberRegistration;

    @Test
    public void testRegister() throws Exception {
        Member newMember = new Member();
        newMember.setName("Jane Doe");
        newMember.setEmail("jane@mailinator.com");
        newMember.setPhoneNumber("2125551234");
        memberRegistration.register(newMember);
        assertNotNull(newMember.getId());
        log.info(newMember.getName() + " was persisted with id " + newMember.getId());
    }
}
```

#### SERVICE

File: `input\kitchensink\src\main\java\org\jboss\as\quickstarts\kitchensink\service\MemberRegistration.java`
```java
package org.example.kitchensink.service;

import org.example.kitchensink.model.Member;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.mongodb.repository.MongoRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.context.ApplicationEventPublisher;

@Service
public class MemberRegistration {

    private static final Logger log = LoggerFactory.getLogger(MemberRegistration.class);

    private final MemberRepository memberRepository;
    private final ApplicationEventPublisher eventPublisher;

    @Autowired
    public MemberRegistration(MemberRepository memberRepository, ApplicationEventPublisher eventPublisher) {
        this.memberRepository = memberRepository;
        this.eventPublisher = eventPublisher;
    }

    @Transactional
    public void register(Member member) throws Exception {
        log.info("Registering " + member.getName());
        memberRepository.save(member);
        eventPublisher.publishEvent(member);
    }
}

interface MemberRepository extends MongoRepository<Member, String> {}
```

#### REPOSITORY

File: `input\kitchensink\src\main\java\org\jboss\as\quickstarts\kitchensink\data\MemberRepository.java`
```java
package org.example.kitchensink.data;

import org.example.kitchensink.model.Member;
import org.springframework.data.mongodb.repository.MongoRepository;
import org.springframework.data.mongodb.repository.Query;
import org.springframework.stereotype.Repository;
import java.util.List;

@Repository
public interface MemberRepository extends MongoRepository<Member, String> {

    @Query("{ 'email' : ?0 }")
    Member findByEmail(String email);

    List<Member> findAllByOrderByNameAsc();
}
```

#### APPLICATION

File: `input\kitchensink\src\test\resources\test-ds.xml`
```java
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.data.mongodb.config.AbstractMongoClientConfiguration;
import org.springframework.data.mongodb.repository.config.EnableMongoRepositories;
import org.springframework.context.annotation.Bean;
import com.mongodb.client.MongoClients;
import com.mongodb.client.MongoClient;
import org.springframework.data.mongodb.core.MongoTemplate;
import org.springframework.beans.factory.annotation.Value;

@SpringBootApplication
@EnableMongoRepositories
public class Application {

    public static void main(String[] args) {
        SpringApplication.run(Application.class, args);
    }

    @Bean
    public MongoClient mongoClient(@Value("${spring.data.mongodb.uri}") String uri) {
        return MongoClients.create(uri);
    }

    @Bean
    public MongoTemplate mongoTemplate() throws Exception {
        return new MongoTemplate(mongoClient(), "kitchensink-quickstart-test");
    }
}

// application.properties
# MongoDB configuration
spring.data.mongodb.uri=mongodb://localhost:27017/kitchensink-quickstart-test

```

#### CONTROLLER

File: `input\kitchensink\src\main\java\org\jboss\as\quickstarts\kitchensink\rest\MemberResourceRESTService.java`
```java
package com.example.memberservice.controller;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.bind.annotation.RestController;

import com.example.memberservice.model.Member;
import com.example.memberservice.repository.MemberRepository;
import com.example.memberservice.service.MemberRegistration;

import javax.validation.ConstraintViolation;
import javax.validation.ConstraintViolationException;
import javax.validation.ValidationException;
import javax.validation.Validator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

@RestController
@RequestMapping("/members")
public class MemberResourceRESTService {

    @Autowired
    private MemberRepository repository;

    @Autowired
    private MemberRegistration registration;

    @Autowired
    private Validator validator;

    @GetMapping
    public List<Member> listAllMembers() {
        return repository.findAllByOrderByNameAsc();
    }

    @GetMapping("/{id}")
    public ResponseEntity<Member> lookupMemberById(@PathVariable String id) {
        return repository.findById(id)
                .map(ResponseEntity::ok)
                .orElse(ResponseEntity.notFound().build());
    }

    @PostMapping
    public ResponseEntity<?> createMember(@Validated @RequestBody Member member) {
        try {
            validateMember(member);
            registration.register(member);
            return ResponseEntity.ok().build();
        } catch (ConstraintViolationException ce) {
            return createViolationResponse(ce.getConstraintViolations());
        } catch (ValidationException e) {
            Map<String, String> responseObj = new HashMap<>();
            responseObj.put("email", "Email taken");
            return ResponseEntity.status(HttpStatus.CONFLICT).body(responseObj);
        } catch (Exception e) {
            Map<String, String> responseObj = new HashMap<>();
            responseObj.put("error", e.getMessage());
            return ResponseEntity.badRequest().body(responseObj);
        }
    }

    private void validateMember(Member member) throws ConstraintViolationException, ValidationException {
        Set<ConstraintViolation<Member>> violations = validator.validate(member);
        if (!violations.isEmpty()) {
            throw new ConstraintViolationException(new HashSet<>(violations));
        }
        if (emailAlreadyExists(member.getEmail())) {
            throw new ValidationException("Unique Email Violation");
        }
    }

    private ResponseEntity<Map<String, String>> createViolationResponse(Set<ConstraintViolation<?>> violations) {
        Map<String, String> responseObj = new HashMap<>();
        for (ConstraintViolation<?> violation : violations) {
            responseObj.put(violation.getPropertyPath().toString(), violation.getMessage());
        }
        return ResponseEntity.badRequest().body(responseObj);
    }

    public boolean emailAlreadyExists(String email) {
        return repository.findByEmail(email).isPresent();
    }
}
```

File: `input\kitchensink\src\main\java\org\jboss\as\quickstarts\kitchensink\controller\MemberController.java`
```java
package com.example.kitchensink.controller;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.servlet.mvc.support.RedirectAttributes;
import com.example.kitchensink.model.Member;
import com.example.kitchensink.service.MemberRegistration;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.http.HttpStatus;

@RestController
@RequestMapping("/members")
public class MemberController {

    private final MemberRegistration memberRegistration;

    @Autowired
    public MemberController(MemberRegistration memberRegistration) {
        this.memberRegistration = memberRegistration;
    }

    @PostMapping("/register")
    @ResponseStatus(HttpStatus.CREATED)
    public ResponseEntity<String> register(@RequestBody Member newMember, RedirectAttributes redirectAttributes) {
        try {
            memberRegistration.register(newMember);
            return ResponseEntity.ok("Registration successful");
        } catch (Exception e) {
            String errorMessage = getRootErrorMessage(e);
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(errorMessage);
        }
    }

    private String getRootErrorMessage(Exception e) {
        String errorMessage = "Registration failed. See server log for more information";
        if (e == null) {
            return errorMessage;
        }
        Throwable t = e;
        while (t != null) {
            errorMessage = t.getLocalizedMessage();
            t = t.getCause();
        }
        return errorMessage;
    }
}
```

#### BUILD

File: `input\kitchensink\pom.xml`
```java
<project xmlns="http://maven.apache.org/POM/4.0.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/maven-v4_0_0.xsd">
    <modelVersion>4.0.0</modelVersion>
    <artifactId>kitchensink</artifactId>
    <version>1.0.0</version>
    <packaging>jar</packaging>
    <name>Quickstart: kitchensink</name>
    <description>A starter Spring Boot application project with MongoDB</description>

    <licenses>
        <license>
            <name>Apache License, Version 2.0</name>
            <url>http://www.apache.org/licenses/LICENSE-2.0.html</url>
            <distribution>repo</distribution>
        </license>
    </licenses>

    <properties>
        <java.version>21</java.version>
        <spring.boot.version>3.2.0</spring.boot.version>
    </properties>

    <dependencies>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-data-mongodb</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-test</artifactId>
            <scope>test</scope>
        </dependency>
    </dependencies>

    <build>
        <plugins>
            <plugin>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-maven-plugin</artifactId>
            </plugin>
        </plugins>
    </build>
</project>
```

#### MODEL

File: `input\kitchensink\src\main\java\org\jboss\as\quickstarts\kitchensink\model\Member.java`
```java
package org.example.kitchensink.model;

import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.mapping.Document;
import org.springframework.data.mongodb.core.mapping.Field;
import jakarta.validation.constraints.Digits;
import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;

@Document(collection = "members")
public class Member {

    @Id
    private String id;

    @NotNull
    @Size(min = 1, max = 25)
    @Pattern(regexp = "[^0-9]*", message = "Must not contain numbers")
    private String name;

    @NotNull
    @NotEmpty
    @Email
    private String email;

    @NotNull
    @Size(min = 10, max = 12)
    @Digits(fraction = 0, integer = 12)
    @Field(name = "phone_number")
    private String phoneNumber;

    public String getId() {
        return id;
    }

    public void setId(String id) {
        this.id = id;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public String getEmail() {
        return email;
    }

    public void setEmail(String email) {
        this.email = email;
    }

    public String getPhoneNumber() {
        return phoneNumber;
    }

    public void setPhoneNumber(String phoneNumber) {
        this.phoneNumber = phoneNumber;
    }
}
```

#### COMPONENT

File: `input\kitchensink\src\main\java\org\jboss\as\quickstarts\kitchensink\data\MemberListProducer.java`
```java
package com.example.kitchensink.data;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.event.EventListener;
import org.springframework.stereotype.Component;
import org.springframework.web.context.annotation.RequestScope;
import java.util.List;

import com.example.kitchensink.model.Member;
import com.example.kitchensink.repository.MemberRepository;

@Component
@RequestScope
public class MemberListProducer {

    private final MemberRepository memberRepository;
    private List<Member> members;

    @Autowired
    public MemberListProducer(MemberRepository memberRepository) {
        this.memberRepository = memberRepository;
        retrieveAllMembersOrderedByName();
    }

    public List<Member> getMembers() {
        return members;
    }

    @EventListener
    public void onMemberListChanged(Member member) {
        retrieveAllMembersOrderedByName();
    }

    public void retrieveAllMembersOrderedByName() {
        members = memberRepository.findAllByOrderByNameAsc();
    }
}
```


### 2.3  Create MongoDB initialization
```
db.createCollection('members');

// Create index on email field
db.members.createIndex({ email: 1 }, { unique: true });

// Insert mock data
db.members.insertMany([
  { name: 'John Doe', email: 'john.doe@example.com', phone_number: '1234567890' },
  { name: 'Jane Smith', email: 'jane.smith@example.com', phone_number: '0987654321' }
]);
```

## 3. Implementation Steps

1. **Set up local environment**
  - Install Java 21 and Maven 3.6.0 or later.

  - Install MongoDB and ensure it is running on localhost:27017.

  - Set up a new Spring Boot project using Spring Initializr with dependencies for Spring Web and Spring Data MongoDB.

2. **Migrate data model to MongoDB**
  - Create a new Member class in the model package with appropriate annotations for MongoDB.

  - Define the MongoDB schema for the Member collection.

3. **Implement repository layer**
  - Create a MemberRepository interface extending MongoRepository.

  - Implement custom query methods as needed.

4. **Implement service layer**
  - Create a MemberRegistration service class to handle member registration logic.

  - Inject the MemberRepository into the service class.

5. **Implement controller layer**
  - Create a MemberController class to handle HTTP requests.

  - Define endpoints for member registration and retrieval.

6. **Set up application configuration**
  - Create an AppConfig class to configure Spring components.

  - Set up MongoDB connection properties in application.properties.

7. **Create data initialization script**
  - Write a script to create the 'members' collection and define indexes on the 'email' field.

  - Insert mock data into the collection for testing.

8. **Implement unit tests**
  - Write unit tests for the Member model, repository, and service classes.

  - Use Mockito to mock dependencies in tests.

9. **Implement integration tests**
  - Write integration tests for the MemberController using TestRestTemplate.

  - Test the full registration flow and ensure data is persisted in MongoDB.

10. **Run and validate application**
  - Run the Spring Boot application.

  - Test the REST endpoints using Postman or a similar tool.


## 4. Additional Considerations
### 4.1 Performance Optimization

  - Use indexes on frequently queried fields to improve read performance.

  - Consider using pagination for large datasets.

### 4.2 Data Migration

  - Plan for migrating existing data from the legacy database to MongoDB.

  - Ensure data integrity during the migration process.

### 4.3 Transaction Support

  - Evaluate the need for transactions in MongoDB and implement if necessary using session support.

### 4.4 Serviceability

  - Implement logging for all service methods to track application behavior.

  - Set up monitoring for MongoDB performance.


## 5. Testing Strategy
1. **Unit Tests:**
  - Test individual methods in the Member model for validation constraints.

  - Mock the MemberRepository in service tests to isolate service logic.


2. **Integration Tests:**
  - Test the full registration flow from the controller to the database.

  - Ensure that the application context loads correctly with all beans.


**Test Class Template:**
```
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.ResponseEntity;
import static org.junit.jupiter.api.Assertions.*;

@SpringBootTest
public class MemberControllerIT {

    @Autowired
    private TestRestTemplate restTemplate;

    @Test
    public void testRegisterMember() {
        Member newMember = new Member();
        newMember.setName("Jane Doe");
        newMember.setEmail("jane.doe@example.com");
        newMember.setPhoneNumber("1234567890");

        ResponseEntity<String> response = restTemplate.postForEntity("/members/register", newMember, String.class);

        assertEquals(200, response.getStatusCodeValue());
    }
}
```