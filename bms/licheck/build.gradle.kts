plugins {
  id("java")
  kotlin("jvm") version "2.0.0"
}

repositories {
  mavenCentral()
}

dependencies {
  testImplementation(platform("org.junit:junit-bom:5.10.2"))
  testImplementation("org.junit.jupiter:junit-jupiter")
  testRuntimeOnly("org.junit.platform:junit-platform-launcher")
  testImplementation("org.jctools:jctools-core:3.1.0")
  testImplementation("com.googlecode.concurrent-trees:concurrent-trees:2.6.1")
  implementation("org.jetbrains.kotlinx:kotlinx-coroutines-core:1.5.0")
}

tasks.register<Copy>("copyDependencies") {
  from(configurations.testRuntimeClasspath)
  from(configurations.testRuntimeClasspath.get().incoming.artifactView {
    withVariantReselection()
    isLenient = true
    attributes {
      attribute(Category.CATEGORY_ATTRIBUTE, objects.named(Category.DOCUMENTATION))
      attribute(DocsType.DOCS_TYPE_ATTRIBUTE, objects.named(DocsType.SOURCES))
    }
  }.files)
  into("${layout.buildDirectory.get().asFile}/dependency")
}

java {
  withSourcesJar()
}

// Copy Java sources into the classes output dirs so build/classes/java contains both .class and .java
tasks.named<JavaCompile>("compileJava").configure {
    doLast {
        copy {
            from(sourceSets.main.get().allSource.matching {
                include("**/*.java")
            })
            // This is typically: project/build/classes/java/main
            into(destinationDirectory.get().asFile)
        }
    }
}

tasks.named<JavaCompile>("compileTestJava").configure {
    doLast {
        copy {
            from(sourceSets.test.get().allSource.matching {
                include("**/*.java")
            })
            // This is typically: project/build/classes/java/test
            into(destinationDirectory.get().asFile)
        }
    }
}
